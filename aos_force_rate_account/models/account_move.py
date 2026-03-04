# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

# class AccountMove(models.Model):
#     _inherit = "account.move"
#     
#     force_rate = fields.Float('Rate Amount', compute='_get_currency_rate', store=True)
#     
#     @api.depends('partner_id', 'currency_id', 'invoice_date')
#     def _get_currency_rate(self):
#         for invoice in self:
#             company_currency = invoice.company_currency_id
#             invoice_currency = invoice.currency_id or company_currency
#             if invoice_currency != company_currency:
#                 invoice.force_rate = invoice_currency.with_context(partner_id=invoice.partner_id.id,date=invoice.date_invoice).compute(1.0, company_currency, round=False)
#             else:
#                 invoice.force_rate = 1.0
    
    
#     def compute_invoice_totals(self, company_currency, invoice_move_lines):
#         total, total_currency, invoice_move_lines = super(AccountMove, self.with_context(force_rate=self.force_rate)).compute_invoice_totals(company_currency=company_currency, invoice_move_lines=invoice_move_lines)
#         #print ('--compute_invoice_totals--',self.force_rate)
#         return total, total_currency, invoice_move_lines
#     
#     
#     def action_move_create(self):
#         result = super(AccountMove, self.with_context(force_rate=self.force_rate)).action_move_create()
#         #print ('--action_move_create--',self.force_rate)
#         return result

# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
    
#     @api.model
#     def _compute_amount_fields(self, amount, src_currency, company_currency):
#         """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
#         debit, credit, amount_currency, currency_id = super(AccountMoveLine, self.with_context(force_rate=self.env.context.get('force_rate')))._compute_amount_fields(amount=amount, src_currency=src_currency, company_currency=company_currency)
#         return debit, credit, amount_currency, currency_id

#     @api.model
#     def _compute_amount_fields(self, amount, src_currency, company_currency):
#         """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
#         #print ('----sss----',self.env.context.get('force_rate'))
#         amount_currency = False
#         currency_id = False
#         date = self.env.context.get('date') or fields.Date.today()
#         company = self.env.context.get('company_id')
#         company = self.env['res.company'].browse(company) if company else self.env.user.company_id
#         if src_currency and src_currency != company_currency:
#             amount_currency = amount
#             amount = src_currency.with_context(force_rate=self.env.context.get('force_rate'))._convert(amount, company_currency, company, date)
#             currency_id = src_currency.id
#         debit = amount > 0 and amount or 0.0
#         credit = amount < 0 and -amount or 0.0
#         return debit, credit, amount_currency, currency_id
    
