import time
from odoo import models,fields
from odoo.exceptions import UserError
import calendar
# import datetime
from datetime import datetime, timedelta
import xlsxwriter
import io
import base64
import os

from babel.dates import format_datetime, format_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class AccountVoucherReportXlsx(models.TransientModel):
    _name = "account.voucher.report.xlsx"
    _description = "Download Report"

    name = fields.Char(string="Filename")
    file = fields.Binary()

class VoucherReportWizard(models.TransientModel):
    _name = "voucher.report.xlsx.wizard"
    _description = "Voucher Report XLSX Wizard"

    date_from = fields.Date(string='Start Date', required=True, default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='End Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    journal_id = fields.Many2one('account.journal', string="Journal", required=True, domain="[('type','in',('cash','bank'))]")
    detail_ok = fields.Boolean('With Details')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    state_ok = fields.Boolean('Separate Confirm & Posted')
    state_confirm = fields.Char()
    state_posted = fields.Char()
    
    def print_report(self):
        # get [start_date,end_date]
        # get_date = self._get_month_and_year(self.start_date,self.end_date)
        #domain = [('state','in',('confirm','posted')),('date','>=',self.date_from), ('date', '<=', self.date_to),('payment_journal_id','=',self.journal_id.id)]
        domain_voucher = [('state','in',('confirm','posted')),('date','>=',self.date_from), ('date', '<=', self.date_to),'|',('payment_journal_id','=',self.journal_id.id),('line_ids.account_id','=',self.journal_id.default_account_id.id)]
        domain_mline = [('move_id.state','=','posted'),('date','>=',self.date_from), ('date', '<=', self.date_to),('account_id','=',self.journal_id.default_account_id.id)]
        # domain =[
        #    ('state_id','=',self.env.ref('aos_support.support_ticket_stage_closed').id),
        #    '&','&','&',('assign_date','!=',False),('close_time','!=',False),
        #    ('problem_assign_date','!=',False),('problem_close_time','!=',False),
        #    ('assign_date','>=',self.start_date), ('assign_date','<=',self.end_date),
        #    ('close_time','<=', self.end_date),
        # ]
        # if self.partner_ids:,
        #     domain.append(('partner_id','in',self.partner_ids.ids))
        # if self.sid:
        #     domain.append(('sid','ilike',self.sid))
        # if self.bandwidth_type:
        #     domain.append(('bandwidth_type','=',self.bandwidth_type))
        vouchers = self.env['account.voucher'].search(domain_voucher, order='date asc')
        move_lines = self.env['account.move.line'].search(domain_mline, order='date asc, move_name desc, debit asc, id')
        # if not tickets:
        #     raise UserError('%d records ticket for %s %s' % (len(tickets),self.start_date.strftime('%B'),self.start_date.year))

        # get range date end_date - start_date
        date = self.date_from - self.date_to
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'journal': self.journal_id,
            'company_name': self.company_id.name,
            #'date': date.days,
            'report_name': self.journal_id.name,#self.start_date.strftime("%b")+' '+ str(self.start_date.year),
            #'range_date': get_date,
        }
        if self.user_has_groups('aos_account_voucher.group_accounting_account_voucher'):
            # report = self.env.ref('aos_account_voucher.account_voucher_monthly_report')
            # service_name = []
            # cid = ''
            # if self.partner_ids:
            #     service_name = list(map(lambda x: x.split('/')[0], tickets.partner_id.mapped('display_name')))
            #     cid = ', '.join(list(set(service_name))[:6])
            # report.sudo()['name'] =  'BUKU KAS'# + (cid if service_name else '') + ' [' + self.start_date.strftime("%B") +'-'+ self.end_date.strftime("%B")+ ' ' + str(self.end_date.year) + ']'
            # return report.report_action(vouchers, data=data)
            excelraw = self.generate_xlsx_report(data=data, vouchers=vouchers, move_lines=move_lines)
            wizard = self.env['account.voucher.report.xlsx'].create({'file':excelraw, 'name':data.get('report_name')+'.xlsx'})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Download Report',
                'res_model': 'account.voucher.report.xlsx',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': wizard.id,
                'target': 'new'
            }
        else:
            raise UserError('Only Support Manager are allowed to print this report')
            

    # def _get_month_and_year(self,start,end):    
    #     get_end_date_from_month =  calendar.monthrange(start.year, start.month)[1] # get 29/30/31
    #     # [Start Date, End Date]
    #     start_date = datetime.datetime(start.year,start.month,start.day,0,0,0).strftime('%d-%B-%Y %H:%M')
    #     end_date = datetime.datetime(end.year,end.month,end.day,23,59,59).strftime('%d-%B-%Y %H:%M')
    #     return [start_date, end_date]

    def _beginning_balance(self, date, journal):
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        res = {}
        beginning_balance = 0.0
        accounts = journal.default_account_id
        context_balance_start = {'strict_range': True, 'date_to': date, 'account_ids': journal.default_account_id}#'date_to': self.date_to{'strict_range': True, 'initial_bal': True, 'date_from': self.date_from, 'date_to': False}
        tables, where_clause, where_params = self.env['account.move.line'].with_context(context_balance_start)._query_get()
        #print ('===context_balance_start==',context_balance_start,date,journal.default_account_id)
        tables = tables.replace('"', '') if tables else "account_move_line"
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                    " FROM " + tables + \
                    " WHERE account_id IN %s " \
                        + filters + \
                    " GROUP BY account_id"
        params = (tuple(accounts._ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            res[row['id']] = row
        
        if res.get(journal.default_account_id.id):
            beginning_balance = res[journal.default_account_id.id]['balance']
        #print ('===res==',res,beginning_balance)
        return beginning_balance

    def generate_xlsx_report(self, data, vouchers, move_lines):
        # for obj in supports:
        fileData = io.BytesIO()
        workbook = xlsxwriter.Workbook(fileData)
        report_name = data.get('report_name')
        # One sheet by partner
        sheet = workbook.add_worksheet(report_name)
        format_sheet = workbook.add_format()
        bold = format_sheet.set_bold(1)
        sheet.set_row(0,18)
        sheet.set_row(1,18)
        sheet.set_row(2,18)
        sheet.set_row(3,22)
        sheet.set_column('A1:A1',10.36)
        sheet.set_column('B1:B1',0.78)
        sheet.set_column('C1:C1',39.64)
        sheet.set_column('D1:D1',2.64)
        sheet.set_column('E1:E1',12.09)
        sheet.set_column('F1:F1',3.64)
        sheet.set_column('G1:G1',15.09)
        sheet.set_column('H1:H1',15.09)
        sheet.set_column('I1:I1',15.82)
        # Start HEADER
        # Title
        title = workbook.add_format({'bold':True, 'align':'center', 'font_size':16})
        sheet.merge_range('A1:I1', '%s' % report_name, title)
        sheet.merge_range('A2:I2', '%s' % data['company_name'], title)
        #sheet.merge_range('A3:I3', 'Per %s - %s' % (data['date_from'].strftime('%d'), data['date_to'].strftime('%d %B %Y')), title)
        #datetime.strptime('2020-04-06 10:00:00', '%Y-%m-%d %H:%M:%S')
        #print ('===DATE===',type(data['date_from']),data['date_to'],data['date_from'].strftime('%Y-%m'))
        #datetime.strftime(sample_date, "%Y-%d-%m %H:%M:%S")
        #data['date_from'].strftime('%Y-%m')
        date_from = datetime.strftime(data['date_from'], '%d')
        date_to = datetime.strftime(data['date_to'],'%d %B %Y')
        sheet.merge_range('A3:I3', 'Per %s - %s' % (date_from, date_to), title)
        sheet.insert_image('A1','aos_account_voucher/static/img/nk_baru.png',{'x_scale': 0.4, 'y_scale': 0.34,'x_offset':60,'y_offset':0,'object_position':1})
        # Header Info 1

        """
            A = 0, B = 1, C = 2, D = 3, E = 4, F = 5, G = 6, H = 7, I = 8, J = 9, K = 10
            L = 11, M = 12, N = 13, O = 14, P = 15, Q = 16, R = 17, S = 18, T = 19, U = 20
            V = 21, W = 22, X = 23, Y = 24, Z = 25
        """

        # END HEADER

        # Main Page
        # Header Main
        header_set = workbook.add_format({'align':'center','valign':'vcenter','bold': True,'bg_color':'gray','border':1,'border_color':'black','color':'white','font_size':11})
        header_number_set = workbook.add_format({'num_format': '#,##0.00', 'bold': True, 'align':'right','valign':'vcenter','bg_color':'gray','border':1,'border_color':'black','color':'white','font_size':11})
        header_wrap = workbook.add_format({'align':'center','valign':'vcenter','bg_color':'gray','border':1,'border_color':'black','color':'white','font_size':11,'text_wrap':True})
        sheet.write('A5','TANGGAL',header_set)
        sheet.write('B5','',header_set)
        sheet.merge_range('C5:E5','URAIAN',header_set)
        sheet.write('F5','NO',header_set)
        sheet.write('G5','DEBIT',header_set)
        sheet.write('H5','KREDIT',header_set)
        sheet.write('I5','SALDO',header_set)
        #looping voucher line
        number = 1
        row = 5
        #beginning_debit = self._beginning_balance(data['date_from'], data['journal'])
        #beginning_credit = 0
        beginning_balance = self._beginning_balance(data['date_from']-timedelta(days=1), data['journal'])
        beginning_debit = self._beginning_balance(data['date_from']-timedelta(days=1), data['journal']) if beginning_balance > 0 else 0
        beginning_credit = self._beginning_balance(data['date_from']-timedelta(days=1), data['journal']) if beginning_balance < 0 else 0
        #currency_format = workbook.add_format({'num_format': '$#,##0.00'})'bold':True,
        base_format = workbook.add_format({'border':0, 'align':'left', 'num_format': '#,##0.00'})
        base_bold_format = workbook.add_format({'bold':True, 'border':0, 'align':'left', 'num_format': '#,##0.00'})
        number_bold_format = workbook.add_format({'border':0, 'bold':True,'align':'right', 'num_format': '#,##0.00'})
        number_format = workbook.add_format({'border':0, 'align':'right', 'num_format': '#,##0.00'})
        sheet.write(row, 0, '', base_format)
        sheet.write(row, 1, '', base_format)
        sheet.write(row, 2, 'Saldo per %s' % data['date_from'], base_bold_format)
        #DETAIL LINE START
        sheet.write(row, 3, '',base_format)
        sheet.write(row, 4, '',base_format)
        #DETAIL LINE END
        sheet.write(row, 5, '', base_format)
        sheet.write(row, 6, beginning_balance if beginning_balance > 0 else '', number_bold_format)
        sheet.write(row, 7, beginning_balance if beginning_balance < 0 else '', number_bold_format)
        sheet.write(row, 8, beginning_balance, number_bold_format)
        row += 1
        row_confirm = []
        row_posted = []
        header_confirm = header_posted = 0
        mutasi_debit = mutasi_credit = 0
        # print ('===vouchers==',vouchers,move_lines,vouchers.mapped('move_id'),move_lines.mapped('move_id'))
        # vouchers 
        if self.journal_id.type == 'cash':
            for voucher in vouchers:
                if not self.state_ok:# and voucher.state == 'posted':
                    #ONLY POSTED
                    sheet.write(row, 0, '%s' % voucher.date.strftime('%d/%m/%Y'), base_format)
                    sheet.write(row, 1, '', base_format)
                    sheet.write(row, 2, voucher.name or voucher.narration or voucher.summary_description or '', base_format)
                    if not self.detail_ok:
                        if voucher.voucher_type == 'purchase':
                            if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                credit = 0.0
                            else:
                                debit = 0.0
                                credit = voucher.amount
                        elif voucher.voucher_type == 'sale':
                            if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                debit = 0.0
                                credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                            else:
                                debit = voucher.amount
                                credit = 0.0
                        sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                        sheet.write(row, 4, sum(voucher.line_ids.mapped('price_subtotal')), number_format)
                        sheet.write(row, 5, voucher.number, base_format)
                        sheet.write(row, 6, debit, number_format)#DEBIT
                        sheet.write(row, 7, credit, number_format)#CREDIT
                        beginning_balance += debit# if voucher.voucher_type == 'sale' else 0
                        beginning_balance -= credit# if voucher.voucher_type == 'purchase' else 0
                        sheet.write(row, 8, beginning_balance, number_format)
                    row += 1
                    #DETAIL LINE START
                    if self.detail_ok:
                        total = 0.0
                        for line in voucher.line_ids:
                            sheet.write(row, 2, line.name or '', base_format)
                            sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                            sheet.write(row, 4, line.price_subtotal, number_format)
                            total += line.price_subtotal
                            row += 1
                        if voucher.voucher_type == 'purchase':
                            if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                credit = 0.0
                            else:
                                debit = 0.0
                                credit = voucher.amount
                        elif voucher.voucher_type == 'sale':
                            if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                debit = 0.0
                                credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                            else:
                                debit = voucher.amount
                                credit = 0.0
                        sheet.write(row, 2, (voucher.name or voucher.narration or voucher.summary_description) if self.detail_ok else 'Jumlah dibayarkan', base_format)
                        sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                        sheet.write(row, 4, total, number_format)
                        sheet.write(row, 5, voucher.number, base_format)
                        #DETAIL LINE END
                        sheet.write(row, 6, debit, number_format)
                        sheet.write(row, 7, credit, number_format)
                        sheet.write(row, 8, beginning_balance, number_format)
                        row += 1
                        number += 1
                    mutasi_debit += debit
                    mutasi_credit += credit
                else:
                    #BOTH CONFIRM & POSTED
                    if voucher.state == 'confirm':
                        row_confirm.append(row)
                        # print ('===row_confirm===',row_confirm,len(row_confirm))
                        if len(row_confirm) == 1:
                            header_confirm = row_confirm
                            sheet.merge_range('A%s:I%s' % (row_confirm[0]+1, row_confirm[0]+1), '%s' % (self.state_confirm or 'Confirm'), header_set)
                            row += 1
                        sheet.write(row, 0, '%s' % voucher.date.strftime('%d/%m/%Y'), base_format)
                        sheet.write(row, 1, '', base_format)
                        sheet.write(row, 2, voucher.name or voucher.narration or voucher.summary_description or '', base_format)
                        if not self.detail_ok:
                            if voucher.voucher_type == 'purchase':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                    credit = 0.0
                                else:
                                    debit = 0.0
                                    credit = voucher.amount
                            elif voucher.voucher_type == 'sale':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = 0.0
                                    credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                else:
                                    debit = voucher.amount
                                    credit = 0.0
                            # mutasi_debit += debit
                            # mutasi_credit += credit
                            beginning_balance += debit
                            beginning_balance -= credit
                            sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                            sheet.write(row, 4, sum(voucher.line_ids.mapped('price_subtotal')), number_format)
                            sheet.write(row, 5, voucher.number, base_format)
                            sheet.write(row, 6, debit, number_format)
                            sheet.write(row, 7, credit, number_format)
                            # beginning_balance += voucher.amount if voucher.voucher_type == 'sale' else 0
                            # beginning_balance -= voucher.amount if voucher.voucher_type == 'purchase' else 0
                            sheet.write(row, 8, beginning_balance, number_format)
                        row += 1
                        #DETAIL LINE START
                        if self.detail_ok:
                            total = 0.0
                            for line in voucher.line_ids:
                                sheet.write(row, 2, line.name or '', base_format)
                                sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                                sheet.write(row, 4, line.price_subtotal, number_format)
                                total += line.price_subtotal
                                row += 1
                            
                            if voucher.voucher_type == 'purchase':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                    credit = 0.0
                                else:
                                    debit = 0.0
                                    credit = voucher.amount
                            elif voucher.voucher_type == 'sale':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = 0.0
                                    credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                else:
                                    debit = voucher.amount
                                    credit = 0.0
                            # mutasi_debit += debit
                            # mutasi_credit += credit
                            beginning_balance += debit
                            beginning_balance -= credit

                            # mutasi_debit += voucher.amount if voucher.voucher_type == 'sale' else 0
                            # mutasi_credit += voucher.amount if voucher.voucher_type == 'purchase' else 0
                            # beginning_balance += voucher.amount if voucher.voucher_type == 'sale' else 0
                            # beginning_balance -= voucher.amount if voucher.voucher_type == 'purchase' else 0
                            sheet.write(row, 2, (voucher.name or voucher.narration or voucher.summary_description) if self.detail_ok else 'Jumlah dibayarkan', base_format)
                            sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                            sheet.write(row, 4, total, number_format)
                            sheet.write(row, 5, voucher.number, base_format)
                            #DETAIL LINE END
                            sheet.write(row, 6, debit, number_format)
                            sheet.write(row, 7, credit, number_format)
                            sheet.write(row, 8, beginning_balance, number_format)
                            row += 1
                            number += 1

                    if voucher.state == 'posted':
                        #sheet.merge_range('C%s:E%s' % (row, row), 'Sudah Realisasi / Siap Jurnal',header_set)
                        # row += 1
                        # sheet.merge_range('A%s:I%s' % (row, row), '%s' % self.state_posted or 'Posted' ,header_set)
                        # row += 1
                        # row += 1
                        row_posted.append(row)
                        if len(row_posted) == 1:
                            header_posted = row_posted
                            sheet.merge_range('A%s:I%s' % (header_posted[0]+1, header_posted[0]+1), '%s' % (self.state_posted or 'Posted'), header_set)
                            row += 1
                        sheet.write(row, 0, '%s' % voucher.date.strftime('%d/%m/%Y'), base_format)
                        sheet.write(row, 1, '', base_format)
                        sheet.write(row, 2, voucher.name or voucher.narration or voucher.summary_description or '', base_format)
                        if not self.detail_ok:
                            if voucher.voucher_type == 'purchase':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                    credit = 0.0
                                else:
                                    debit = 0.0
                                    credit = voucher.amount
                            elif voucher.voucher_type == 'sale':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = 0.0
                                    credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                else:
                                    debit = voucher.amount
                                    credit = 0.0
                            sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                            sheet.write(row, 4, sum(voucher.line_ids.mapped('price_subtotal')), number_format)
                            sheet.write(row, 5, voucher.number, base_format)
                            sheet.write(row, 6, debit, number_format)
                            sheet.write(row, 7, credit, number_format)
                            beginning_balance += debit
                            beginning_balance -= credit
                            sheet.write(row, 8, beginning_balance, number_format)
                        row += 1
                        #DETAIL LINE START
                        if self.detail_ok:
                            total = 0.0
                            for line in voucher.line_ids:
                                sheet.write(row, 2, line.name or '', base_format)
                                sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                                sheet.write(row, 4, line.price_subtotal, number_format)
                                total += line.price_subtotal
                                row += 1
                            if voucher.voucher_type == 'purchase':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                    credit = 0.0
                                else:
                                    debit = 0.0
                                    credit = voucher.amount
                            elif voucher.voucher_type == 'sale':
                                if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                                    debit = 0.0
                                    credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                                else:
                                    debit = voucher.amount
                                    credit = 0.0
                            # mutasi_debit += debit
                            # mutasi_credit += credit
                            beginning_balance += debit
                            beginning_balance -= credit
                            # mutasi_debit += voucher.amount if voucher.voucher_type == 'sale' else 0
                            # mutasi_credit += voucher.amount if voucher.voucher_type == 'purchase' else 0
                            # beginning_balance += voucher.amount if voucher.voucher_type == 'sale' else 0
                            # beginning_balance -= voucher.amount if voucher.voucher_type == 'purchase' else 0
                            sheet.write(row, 2, (voucher.name or voucher.narration or voucher.summary_description) if self.detail_ok else 'Jumlah dibayarkan', base_format)
                            sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                            sheet.write(row, 4, total, number_format)
                            sheet.write(row, 5, voucher.number, base_format)
                            #DETAIL LINE END
                            sheet.write(row, 6, debit, number_format)
                            sheet.write(row, 7, credit, number_format)
                            sheet.write(row, 8, beginning_balance, number_format)
                            row += 1
                            number += 1
                    mutasi_debit += debit
                    mutasi_credit += credit
        else:
            for mline in move_lines:
                if not self.state_ok:# and voucher.state == 'posted':
                    #ONLY POSTED
                    sheet.write(row, 0, '%s' % mline.date.strftime('%d/%m/%Y'), base_format)
                    sheet.write(row, 1, '', base_format)
                    sheet.write(row, 2, mline.name or '', base_format)
                    if not self.detail_ok:
                        # if voucher.voucher_type == 'purchase':
                        #     if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                        #         debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                        #         credit = 0.0
                        #     else:
                        #         debit = 0.0
                        #         credit = voucher.amount
                        # elif voucher.voucher_type == 'sale':
                        #     if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                        #         debit = 0.0
                        #         credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                        #     else:
                        #         debit = voucher.amount
                        #         credit = 0.0
                        debit = mline.debit or 0
                        credit = mline.credit or 0
                        sheet.write(row, 3, mline.currency_id.symbol, base_format)
                        sheet.write(row, 4, abs(mline.debit - mline.credit), number_format)
                        sheet.write(row, 5, mline.move_id.name, base_format)
                        sheet.write(row, 6, mline.debit if mline.debit > 0 else 0, number_format)#DEBIT
                        sheet.write(row, 7, mline.credit if mline.credit > 0 else 0, number_format)#CREDIT
                        beginning_balance += debit# if voucher.voucher_type == 'sale' else 0
                        beginning_balance -= credit# if voucher.voucher_type == 'purchase' else 0
                        sheet.write(row, 8, beginning_balance, number_format)
                    row += 1
                    #DETAIL LINE START
                    # if self.detail_ok:
                    #     total = 0.0
                    #     for line in voucher.line_ids:
                    #         sheet.write(row, 2, line.name or '', base_format)
                    #         sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                    #         sheet.write(row, 4, line.price_subtotal, number_format)
                    #         total += line.price_subtotal
                    #         row += 1
                    #     if voucher.voucher_type == 'purchase':
                    #         if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                    #             debit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                    #             credit = 0.0
                    #         else:
                    #             debit = 0.0
                    #             credit = voucher.amount
                    #     elif voucher.voucher_type == 'sale':
                    #         if sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal')):
                    #             debit = 0.0
                    #             credit = sum(voucher.line_ids.filtered(lambda il: il.account_id == self.journal_id.default_account_id).mapped('price_subtotal'))
                    #         else:
                    #             debit = voucher.amount
                    #             credit = 0.0
                    #     sheet.write(row, 2, (voucher.name or voucher.narration or voucher.summary_description) if self.detail_ok else 'Jumlah dibayarkan', base_format)
                    #     sheet.write(row, 3, voucher.currency_id.symbol, base_format)
                    #     sheet.write(row, 4, total, number_format)
                    #     sheet.write(row, 5, voucher.number, base_format)
                    #     #DETAIL LINE END
                    #     sheet.write(row, 6, debit, number_format)
                    #     sheet.write(row, 7, credit, number_format)
                    #     sheet.write(row, 8, beginning_balance, number_format)
                    #     row += 1
                    #     number += 1
                    mutasi_debit += debit
                    mutasi_credit += credit
        # print ('===header_confirm==',header_confirm,header_posted)
        # if row_confirm and row_confirm[0]:
        #     sheet.merge_range('A%s:I%s' % (row_confirm[0]+1, row_confirm[0]+1), '%s' % (self.state_confirm or 'Confirm'), header_set)
        # if row_posted and row_posted[0]:
        #     sheet.merge_range('A%s:I%s' % (row_posted[0]+1, row_posted[0]+1), '%s' % (self.state_posted or 'Posted'), header_set)
        # row += 1
        #FOOTER
        sheet.write(row, 0, '', header_set)
        sheet.write(row, 1, '', header_set)
        sheet.write(row, 2, '', header_set)
        sheet.write(row, 3, '', header_set)
        sheet.write(row, 4, '', header_set)
        sheet.write(row, 5, '', header_set)
        sheet.write(row, 6, mutasi_debit + beginning_debit, header_number_set)
        sheet.write(row, 7, mutasi_credit + beginning_credit, header_number_set)
        sheet.write(row, 8, beginning_balance, header_number_set)
        row += 1
        #CLOSE XLSX
        workbook.close()
        fileData.seek(0)
        return base64.encodebytes(fileData.read())
            
    # def _count_float_to_time(self,duration):
    #     time = []
    #     tsec = duration.total_seconds()
    #     hh = int(tsec // 3600)
    #     mm = int((tsec % 3600) // 60)
    #     ss = int((tsec % 3600) % 60)
    #     return f"{'0%d' % (hh) if hh < 10 else hh}:{'0%d' % (mm) if mm < 10 else mm}:{'0%d' % (ss) if ss < 10 else ss}"
