from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    ''' Defining a student information '''
    _name = "account.move"
    _inherit = ['account.move']

    aged_due = fields.Char('Aged fr Due', compute='_get_aged_due', store=False)
    aged_payment_due = fields.Char('Aged Payment Due', compute='_get_aged_due', store=False)

    @api.depends('invoice_date', 'invoice_date_due', )
    def _get_aged_due(self):
        for invoice in self:
            invoice.aged_due = '0 Days'
            invoice.aged_payment_due = '0 Days'
            #payment = invoice.line_ids.mapped('payment_id')
            payment_date = invoice._get_reconciled_info_JSON_values()
            #print ('===payment===',payment_date)#,payment_widget,invoice.invoice_date_due,invoice.state,invoice.invoice_payment_state)
            if invoice.invoice_date and invoice.state == 'posted':
                date_date_from = fields.Date.from_string(fields.Date.today())
                date_date_to = fields.Date.from_string(invoice.invoice_date)
                date_diff_days = (date_date_to - date_date_from).days
                invoice.aged_due = str(date_diff_days) + ' Day'
            if invoice.invoice_date and invoice.payment_state == 'paid' and payment_date:
                date_date_from = fields.Date.from_string(payment_date[0]['date'])
                date_date_to = fields.Date.from_string(invoice.invoice_date)
                date_diff_days = (date_date_to - date_date_from).days
                invoice.aged_payment_due = str(date_diff_days) + ' Day'

    
