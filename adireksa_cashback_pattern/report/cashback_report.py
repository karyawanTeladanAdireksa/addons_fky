# -*- coding: utf-8 -*-
import time
import math
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class ReportCashback(models.AbstractModel):
    _name = 'report.adireksa_cashback_pattern.report_cashback_new'

    def get_report_datas(self, data, mcc):
        cr = self.env.cr
        date_from = data['date_from']
        date_to = data['date_to']
        lines = []
        cashback_in = 0.0
        cashback_used = 0.0
        query = """SELECT 1 as a, cl.name as name, cl.date, cl.reference as reference,
            (case when ct.default_posting = 'debit' then cl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then cl.value else 0 end) as credit,
            0 as invoice_id, 0 as payment_id, 0 as cb_id
            from cashback_lines cl 
            inner join cashback_type ct on ct.id = cl.type_id 
            where cl.cashback_id = {0} and cl.date between '{1}' and '{2}' and cl.state='approve'
            union ALL
            select 2 as a, mcl.reference as name, mcl.date, mcl.reference as reference,
            (case when ct.default_posting = 'debit' then mcl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then mcl.value else 0 end) as credit,
            0 as invoice_id, 0 as payment_id, 0 as cb_id
            from manual_cashback_lines mcl
            inner join cashback_type ct on ct.id = mcl.type_id 
            where mcl.cashback_id = {0} and mcl.date between '{1}' and '{2}' and mcl.state='approve'
            union ALL
            select 3 as a, 'Automatic Cashback' as name, acl.date, acl.reference as reference,
            (case when ct.default_posting = 'debit' then acl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then acl.value else 0 end) as credit,
            0 as invoice_id, 0 as payment_id, 0 as cb_id
            from automatic_cashback_lines acl 
            inner join cashback_type ct on ct.id = acl.type_id 
            where acl.cashback_id = {0} and acl.date between '{1}' and '{2}' and acl.state='approve'
            union ALL
            select 4 as a, 'Pelunasan Invoice dan Promo' as name, pcl.date,
            (case when crl.trigger = 'invoice' then CONCAT('No. Faktur: ', ai.number) 
            else pcl.reference end) as reference,
            (case when ct.default_posting = 'debit' then pcl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then pcl.value else 0 end) as credit,
            pcl.invoice_id as invoice_id, pcl.payment_id as payment_id, cashback_rule_id as cb_id
            from payment_cashback_lines pcl 
            inner join cashback_type ct on ct.id = pcl.type_id 
            inner join account_invoice ai on ai.id = pcl.invoice_id
            inner join cashback_rule_line crl on crl.id = pcl.cashback_rule_id 
            where pcl.cashback_id = {0} and pcl.date between '{1}' and '{2}' and pcl.state='approve'
            order by date""".format(mcc.id, date_from, date_to)
        cr.execute(query)
        res = cr.dictfetchall()
        if res:
            for rs in res:
                if rs['a'] == 1:
                    cr.execute("""SELECT amount_total as total 
                        FROM account_invoice WHERE number='{0}'""".format(rs['name']))
                    rec = cr.dictfetchone()
                    ref = 'Customer Invoice, Total: Rp. %s' % ('{:0,.0f}'.format(rec['total'])) if rec else rs['reference'] 
                elif rs['a'] == 4:
                    invoice = self.env['account.invoice'].browse(rs['invoice_id'])
                    cr.execute("""SELECT apr.amount as amount, paml.date
                        FROM account_partial_reconcile apr
                        INNER JOIN account_move_line paml ON paml.id = apr.credit_move_id
                        INNER JOIN account_move_line iaml ON iaml.id = apr.debit_move_id 
                        WHERE iaml.invoice_id = {0} and paml.payment_id = {1}""".format(rs['invoice_id'], rs['payment_id']))
                    res = cr.dictfetchone()
                    payment_amount = res['amount'] if res['amount'] else 0.0
                    pdate = res['date'] if res['date'] else False
                    if pdate:
                        payment_date = datetime.strptime(pdate, '%Y-%m-%d')
                        curr_date = datetime.strptime(invoice.date_invoice, '%Y-%m-%d')
                        date_diff = abs((payment_date - curr_date).days)
                    else:
                        date_diff = 0
                    ref = '%s (%d hari)' % (rs['reference'], date_diff)
                else:
                    ref = rs['reference']
                cdate = (datetime.strptime(rs['date'], '%Y-%m-%d')).strftime('%d/%m/%Y')
                lines.append({
                    'name': rs['name'],
                    'date': cdate,
                    'ref': ref,
                    'debit': '{:0,.0f}'.format(rs['debit']),
                    'credit': '{:0,.0f}'.format(rs['credit'])
                })
                cashback_in += rs['debit']
                cashback_used += rs['credit']
        query_prev_bal = """SELECT COALESCE(SUM(x.debit),0) as debit, COALESCE(SUM(x.credit),0) as credit
            FROM (select (case when ct.default_posting = 'debit' then cl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then cl.value else 0 end) as credit
            from cashback_lines cl 
            inner join cashback_type ct on ct.id = cl.type_id 
            where cl.cashback_id = {0} and cl.date < '{1}' and cl.state='approve'
            union ALL
            select (case when ct.default_posting = 'debit' then mcl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then mcl.value else 0 end) as credit
            from manual_cashback_lines mcl
            inner join cashback_type ct on ct.id = mcl.type_id 
            where mcl.cashback_id = {0} and mcl.date < '{1}' and mcl.state='approve'
            union ALL
            select (case when ct.default_posting = 'debit' then acl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then acl.value else 0 end) as credit
            from automatic_cashback_lines acl 
            inner join cashback_type ct on ct.id = acl.type_id 
            where acl.cashback_id = {0} and acl.date < '{1}' and acl.state='approve'
            union ALL
            select (case when ct.default_posting = 'debit' then pcl.value else 0 end) as debit,
            (case when ct.default_posting = 'credit' then pcl.value else 0 end) as credit
            from payment_cashback_lines pcl 
            inner join cashback_type ct on ct.id = pcl.type_id 
            where pcl.cashback_id = {0} and pcl.date < '{1}' and pcl.state='approve') x""".format(mcc.id, date_from)
        cr.execute(query_prev_bal)
        rpb = cr.dictfetchone()
        prev_balance =  (rpb['debit'] - rpb['credit']) if rpb else 0
        balance = prev_balance + cashback_in - cashback_used
        mdate = (datetime.strptime(mcc.date, '%Y-%m-%d')).strftime('%d/%m/%Y')
        dfrom = (datetime.strptime(date_from, '%Y-%m-%d')).strftime('%d/%m/%Y')
        dto = (datetime.strptime(date_to, '%Y-%m-%d')).strftime('%d/%m/%Y')
        result = {
            'code': mcc.name,
            'date': mdate,
            'group': mcc.group_id.name,
            'company': mcc.company_id.name,
            'period': '%s - %s' % (dfrom, dto),
            'prev_balance': '{:0,.0f}'.format(prev_balance),
            'cashback_in': '{:0,.0f}'.format(cashback_in),
            'cashback_used': '{:0,.0f}'.format(cashback_used),
            'balance': '{:0,.0f}'.format(balance),
            'lines': lines,
        }
        return result

    @api.model
    def render_html(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.get_report_datas(data.get('form'), docs)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'records': report_lines,
        }
        return self.env['report'].render('adireksa_cashback_pattern.report_cashback_new', docargs)
