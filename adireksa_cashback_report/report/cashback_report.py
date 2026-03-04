# -*- coding: utf-8 -*-
import time
import math
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class ReportCashback(models.AbstractModel):
    _name = 'report.adireksa_cashback_report.cashback_report_template'

    def get_report_datas(self, data, mcc):
        cr = self.env.cr
        date_from = data['date_from']
        date_to = data['date_to']
        previous_balance = data['previous_balance']
        lines = []
        cashback_in = 0.0
        cashback_used = 0.0
        query = """SELECT 1 as a, cl.name as name, cl.date, cl.reference as reference,
            cl.cashback_rule as cashback_rule,cl.days as days,account.name as account,
            (case when cl.default_posting = 'debit' then cl.value else 0 end) as debit,
            (case when cl.default_posting = 'credit' then cl.value else 0 end) as credit, 
            0 as invoice_id, 0 as payment_id, 0 as cb_id
            from cashback_lines cl
			left join account_move account on account.id = cl.account_id
            where cl.cashback_id = {0} and cl.date between '{1}' and '{2}' and cl.state='approve'
            order by date""".format(mcc.id, date_from, date_to)
        cr.execute(query)
        res = cr.dictfetchall()
        if res:
            for rs in res:
                if rs['a'] == 1:
                    cr.execute("""SELECT amount_total as total 
                        FROM account_move WHERE name='{0}'""".format(rs['name']))
                    rec = cr.dictfetchone()
                    ref = 'Customer Invoice, Total: Rp. %s' % ('{:0,.0f}'.format(rec['total'])) if rec else rs['reference'] 
                elif rs['a'] == 4:
                    invoice = self.env['account.move'].browse(rs['invoice_id'])
                    cr.execute("""SELECT apr.amount as amount, paml.date
                        FROM account_partial_reconcile apr
                        INNER JOIN account_move_line paml ON paml.id = apr.credit_move_id
                        INNER JOIN account_move_line iaml ON iaml.id = apr.debit_move_id 
                        WHERE iaml.move_id = {0} and paml.payment_id = {1}""".format(rs['move_id'], rs['payment_id'])) 
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
                
                cashback_rule = rs['cashback_rule']
                days = rs['days']
                account = rs['account']
                cdate = (datetime.strptime(str(rs['date']), '%Y-%m-%d')).date()
                # jika field value bernilai 0 maka jangan tampilkan didalam 
                if rs['debit'] == False and rs['credit'] == False:
                    continue
                lines.append({
                    'name': rs['name'],
                    'date': cdate,
                    'ref': ref,
                    'cashback_rule':cashback_rule,
                    'days':days,
                    'account':account,
                    'debit': '{:0,.0f}'.format(rs['debit']),
                    'credit': '{:0,.0f}'.format(rs['credit'])
                })
                cashback_in += rs['debit']
                cashback_used += rs['credit']
        query_prev_bal = """SELECT COALESCE(SUM(x.debit),0) as debit, COALESCE(SUM(x.credit),0) as credit
            FROM (select (case when cl.default_posting = 'debit' then cl.value else 0 end) as debit,
            (case when cl.default_posting = 'credit' then cl.value else 0 end) as credit
            from cashback_lines cl 
            where cl.cashback_id = {0} and cl.date < '{1}' and cl.state='approve') x""".format(mcc.id, date_from)
        cr.execute(query_prev_bal)
        rpb = cr.dictfetchone()
        # prev_balance =  (rpb['debit'] - rpb['credit']) if rpb else 0
        # balance = rs['balance']
        # mdate = (datetime.strptime('%Y-%m-%d')).strftime('%d/%m/%Y') 
        dfrom = (datetime.strptime(date_from, '%Y-%m-%d')).strftime('%d/%m/%Y')
        dto = (datetime.strptime(date_to, '%Y-%m-%d')).strftime('%d/%m/%Y')
        result = {
            'code': mcc.name,
            'group': mcc.group_id.name,
            'company': mcc.company_id.name,
            'period': '%s - %s' % (dfrom, dto),
            'previous_balance': '{:0,.0f}'.format(previous_balance),
            'cashback_in': '{:0,.0f}'.format(cashback_in),
            'cashback_used': '{:0,.0f}'.format(cashback_used),
            'balance': '{:0,.0f}'.format(previous_balance + cashback_in - cashback_used), 
            'lines': lines,
        }
        return result
 
    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        # self.model = self.env.context.get('active_model')
        # docs = self.env[self.model].browse(self.env.context.get('active_id'))
        docs = self.env['master.customer.cashback'].browse(self.env.context.get('active_id')) 
        report_lines = self.get_report_datas(data.get('form'), docs)
        docargs = { 
            'doc_ids': docids,
            'doc_model': 'master.customer.cashback',
            'data': data['form'], 
            'docs': docs,
            'time': time,
            'records': report_lines, 
        } 
        return docargs


# QUERY 1

# select 2 as a, mcl.reference as name, mcl.date, mcl.reference as reference,
#             (case when mcl.default_posting = 'debit' then mcl.value else 0 end) as debit,
#             (case when mcl.default_posting = 'credit' then mcl.value else 0 end) as credit,
#             0 as invoice_id, 0 as payment_id, 0 as cb_id
#             from manual_cashback_lines mcl
#             where mcl.cashback_id = {0} and mcl.date between '{1}' and '{2}' and mcl.state='approve' 
#             union ALL

#             select 3 as a, 'Automatic Cashback' as name, acl.date, acl.reference as reference,
#             (case when acl.default_posting = 'debit' then acl.value else 0 end) as debit,
#             (case when acl.default_posting = 'credit' then acl.value else 0 end) as credit,
#             0 as invoice_id, 0 as payment_id, 0 as cb_id 
#             from automatic_cashback_lines acl 
#             where acl.cashback_id = {0} and acl.date between '{1}' and '{2}' and acl.state='approve'





# QUERY 2

# select (case when mcl.default_posting = 'debit' then mcl.value else 0 end) as debit,
#             (case when mcl.default_posting = 'credit' then mcl.value else 0 end) as credit
#             from manual_cashback_lines mcl
#             where mcl.cashback_id = {0} and mcl.date < '{1}' and mcl.state='approve'
#             union ALL
#             select (case when acl.default_posting = 'debit' then acl.value else 0 end) as debit,
#             (case when acl.default_posting = 'credit' then acl.value else 0 end) as credit
#             from automatic_cashback_lines acl 
#             where acl.cashback_id = {0} and acl.date < '{1}' and acl.state='approve') x