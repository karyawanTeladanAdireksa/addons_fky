# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil import parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import ValidationError

class CustomerInvoicePrint(models.TransientModel):
    _name = 'customer.invoice.unpaid.report'
    _description = 'customer.invoice.unpaid.report'

    partner_id = fields.Many2one('res.partner', string='Customer',tracking=True,required=True)     
    start_date = fields.Date(
         string='From Date',
         default=lambda *a: (parser.parse(datetime.now().strftime(DF)))
         )
    end_date = fields.Date(
         string='To Date',
         default=lambda *a: (parser.parse(datetime.now().strftime(DF)))
         )
    all_date = fields.Boolean('All Date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    cust_invoice_ids = fields.Many2many('account.move', string='Customer Invoice Unpaid', track_visibility='onchange')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,help='Utility field to express amount currency')
    subtotal = fields.Monetary(string='Total', currency_field='company_currency_id')


    # @api.depends('partner_id')
    # def _compute_invoice_ids(self):
    #     if self.partner_id:
    #         temp = self.env['account.move'].search(['&','&',('state','=','posted'),('move_type','=','out_invoice'),('payment_state','!=','paid'),('company_id','=',self.company_id.id),('partner_id','=',self.partner_id.id)], order='invoice_date desc')
    #         if temp:
    #             self.cust_invoice_ids = temp.ids
    #         else :
    #             self.cust_invoice_ids = False
    #     else :
    #         self.cust_invoice_ids = False
            

    def print_unpaid_invoice(self): 
        if self.all_date and self.partner_id:  
            temp = self.env['account.move'].search(['&','&',('state','=','posted'),('move_type','=','out_invoice'),('payment_state','!=','paid'),('company_id','=',self.company_id.id),('partner_id','=',self.partner_id.id)], order='invoice_date desc')
            if temp:
                self.cust_invoice_ids = temp.ids
                self.subtotal = sum(temp.mapped('amount_total_signed'))
            else :
                self.cust_invoice_ids = False
            # else :
            #     raise ValidationError("Choose Customer!")
        elif self.start_date and self.end_date and self.partner_id: 
            temp = self.env['account.move'].search(['&','&','&','&',('state','=','posted'),('payment_state','!=','paid'),('move_type','=','out_invoice'),('company_id','=',self.company_id.id),('partner_id','=',self.partner_id.id),('invoice_date','>=',self.start_date),('invoice_date','<=',self.end_date)], order='invoice_date desc')
            if temp:
                self.cust_invoice_ids = temp.ids
                self.subtotal = sum(temp.mapped('amount_total_signed'))
            else :
                self.cust_invoice_ids = False
            # else :
            #     raise ValidationError("Choose Customer!")
        else:
            raise ValidationError("Choose Date!")
        return self.env.ref('adireksa_cust_receipt_modifier.action_report_adireksa_customer_invoice').report_action(self)
    
    @api.onchange('company_id')
    def set_domain_customer(self):
        temp = self.env['res.partner'].search([('company_id.id','=',self.company_id.id)])
        temp_list = []
        for data in temp:
            temp_list.append(data.id)
        # res = {} 
        # res['domain'] = {'partner_id':[('id','in',temp_list)]}
        return 