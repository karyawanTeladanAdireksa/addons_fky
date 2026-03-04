# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

class AccountAssignMoveLine(models.TransientModel):
    _name = "account.assign.move.line"
    _description = 'Invoice Line'

#     product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
#     quantity = fields.Float("Quantity", digits='Product Unit of Measure', required=True)
#     uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='move_id.product_uom', readonly=False)
    wizard_id = fields.Many2one('account.assign.invoice', string="Wizard")
#     move_id = fields.Many2one('stock.move', "Move")
    
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
#     move_currency_id = fields.Many2one('res.currency', string='Invoice Currency', compute='_compute_invoice_currency')
    date = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    type = fields.Selection([('dr', 'Debit'),('cr','Credit')], 'Type')
    payment_id = fields.Many2one('account.payment', string='Payment')
    payment_currency_id = fields.Many2one('res.currency', string='Currency')
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', string='Currency')
    name = fields.Char(string='Description', required=False)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    amount_total = fields.Float('Original Amount', required=False, digits='Account')
    residual = fields.Float('Outstanding Amount', required=False, digits='Account')
#     reconcile = fields.Boolean('Full Payment')
#     amount_to_pay = fields.Float('Allocation', required=True, digits='Account')
#     statement_line_id = fields.Many2one('account.bank.statement.line', string='Statement Line')
#     payment_difference = fields.Monetary(compute='_compute_payment_difference', string='Payment Difference', readonly=True, store=True)
#     payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid'),
#                                                     ], 
#                                                    default='open', string="Write-off", copy=False)
#     writeoff_account_id = fields.Many2one('account.account', string="Write-off Account", domain=[('deprecated', '=', False)], copy=False)
#     to_reconcile = fields.Boolean('To Pay')

class AccountAssignInvoice(models.TransientModel):
    _name = 'account.assign.invoice'
    _description = 'Account Assign Invoices'
    
    @api.model
    def default_get(self, fields):
        res = super(AccountAssignInvoice, self).default_get(fields)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'account.payment':
            payment = self.env['account.payment'].browse(self.env.context.get('active_id'))
            if payment.exists():
                res.update({'payment_id': payment.id})
        return res
    
    payment_id = fields.Many2one('account.payment')
    move_lines = fields.One2many('account.assign.move.line', 'wizard_id', 'Outstanding Invoice')
    
    def _prepare_account_move_line(self, payment, line):
        data = {
            'payment_id': payment.id,
            'move_line_id': line.id,
            'date':line.date,
            'date_due':line.date_maturity or line.date,
            'type': line.debit and 'dr' or 'cr',
            'invoice_id': line.move_id.id,
            'name': line.move_id.name or line.name or '/',
        }
        company_currency = payment.journal_id.company_id.currency_id
        payment_currency = payment.currency_id or company_currency
        if line.currency_id and payment_currency==line.currency_id:
            data['amount_total'] = abs(line.amount_currency)
            data['residual'] = abs(line.amount_residual_currency)
            #data['amount_to_pay'] = 0.0#abs(line.amount_residual_currency)
        else:
            #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
            data['amount_total'] = company_currency.compute(line.credit or line.debit or 0.0, payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
            data['residual'] = company_currency.compute(abs(line.amount_residual), payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx)
            #data['amount_to_pay'] = 0.0#company_currency.compute(abs(line.amount_residual), payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
        #line.payment_id = self.id
        return data
    
    @api.onchange('payment_id')
    def _onchange_payment_id(self):
        move_lines = [(5,)]
        payment = self.payment_id
        account_id = payment.destination_account_id or False
        if payment and payment.state != 'draft':
            raise UserError(_("You may only get Outstanding Invoice for Draft payment."))
        #_set_outstanding_lines(payment.partner_id, account_id, payment.currency_id, payment.journal_id, payment.payment_date)
        for line in payment._get_outstanding_lines(payment.partner_id, account_id, payment.currency_id, payment.journal_id, payment.payment_date):
            move_lines.append((0, 0, self._prepare_account_move_line(payment, line)))
        if self.payment_id:
            self.move_lines = move_lines
        
    def _prepare_assign_move_line(self, payment, line):
        data = {
            'move_line_id': line.id,
            'date':line.date,
            'date_due':line.date_maturity or line.date,
            'type': line.debit and 'dr' or 'cr',
            'invoice_id': line.move_id.id,
            'name': line.move_id.name or line.name or '/',
        }
        #print ('----_prepare_assign_move_line---',data)
        company_currency = payment.journal_id.company_id.currency_id
        payment_currency = payment.currency_id or company_currency
        if line.currency_id and payment_currency==line.currency_id:
            data['amount_total'] = abs(line.amount_currency)
            data['residual'] = abs(line.amount_residual_currency)
            data['amount_to_pay'] = 0.0#abs(line.amount_residual_currency)
        else:
            #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
            data['amount_total'] = company_currency.compute(line.credit or line.debit or 0.0, payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
            data['residual'] = company_currency.compute(abs(line.amount_residual), payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx)
            data['amount_to_pay'] = 0.0#company_currency.compute(abs(line.amount_residual), payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
        line.payment_line_id = payment.id
        return data
            
    def confirm_invoice(self): 
        payment = self.payment_id
        new_lines = self.env['account.payment.line']
        for line in self.move_lines:
            if line.move_line_id not in payment.register_ids.mapped('move_line_id'):
                data = self._prepare_assign_move_line(payment, line.move_line_id)
                new_line = new_lines.new(data)
                new_lines += new_line
        payment.register_ids += new_lines
        
#     @api.model
#     def _prepare_outstanding_invoice_from_move_line(self, line):
# #         quantity = line.product_qty - sum(
# #             stock_move.move_dest_ids
# #             .filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
# #             .mapped('move_line_ids.product_qty')
# #         )
# #         quantity = float_round(quantity, precision_rounding=stock_move.product_uom.rounding)
#         return {
#             'move_line_id': line.id,
#         }

#     def _default_next_serial_count(self):
#         move = self.env['stock.move'].browse(self.env.context.get('default_move_id'))
#         if move.exists():
#             filtered_move_lines = move.move_line_ids.filtered(lambda l: not l.lot_name and not l.lot_id)
#             return len(filtered_move_lines)
# 
#     product_id = fields.Many2one('product.product', 'Product',
#         related='move_id.product_id', required=True)
#     move_id = fields.Many2one('stock.move', required=True)
#     next_serial_number = fields.Char('First SN', required=True)
#     next_serial_count = fields.Integer('Number of SN',
#         default=_default_next_serial_count, required=True)
# 
#     @api.constrains('next_serial_count')
#     def _check_next_serial_count(self):
#         for wizard in self:
#             if wizard.next_serial_count < 1:
#                 raise ValidationError(_("The number of Serial Numbers to generate must greater than zero."))
# 
#     def generate_serial_numbers(self):
#         self.ensure_one()
#         self.move_id.next_serial = self.next_serial_number or ""
#         return self.move_id._generate_serial_numbers(next_serial_count=self.next_serial_count)

# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#     
#     assign_id = fields.Many2one('account.assign.invoice', string='Assigned Invoice')

    