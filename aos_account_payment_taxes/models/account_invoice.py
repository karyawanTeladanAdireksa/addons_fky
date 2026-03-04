# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2017 Alphasoft
#    (<https://www.alphasoft.co.id/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import json
from odoo import api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.depends('invoice_line_ids.price_subtotal', 
                 'invoice_line_ids.invoice_line_wth_tax_ids',
                 #'invoice_line_ids.tax_amount_json',
                 #'invoice_line_ids.amount_wth_line', 
                 #'invoice_line_ids.invoice_line_oth_ids', 
                 #'invoice_line_ids.amount_oth_line',
                 'amount_total', 'currency_id', 'company_id')
    def _compute_amount_wth(self):
        #self.net_pay = self.amount_total - self.amount_wht
        #self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        for move in self:
            #print ('==amount_wth_line==',[json.loads(line.tax_amount_json)['amount_wth_line'] for line in move.invoice_line_ids])
            #print ('==amount_oth_line==',[json.loads(line.tax_amount_json)['amount_oth_line'] for line in move.invoice_line_ids])
            #move.amount_tax_wth = sum([json.loads(line.tax_amount_json)['amount_wth_line'] for line in move.invoice_line_ids])#sum(line.amount_wth_line for line in move.invoice_line_ids.filtered(lambda l: l.invoice_line_wth_tax_ids.filtered(lambda t: t.is_withholding)))
            #move.amount_others = sum([json.loads(line.tax_amount_json)['amount_oth_line'] for line in move.invoice_line_ids])#sum(line.amount_oth_line for line in move.invoice_line_ids.filtered(lambda l: l.invoice_line_wth_tax_ids.filtered(lambda t: t.is_expenses)))
            move.amount_tax_wth = sum(line.amount_wth_line for line in move.invoice_line_ids.filtered(lambda l: l.invoice_line_wth_tax_ids.filtered(lambda t: t.is_withholding)))
            # move.amount_others = sum(line.tax_amount_json['amount_oth_line'] for line in move.invoice_line_ids.filtered(lambda l: l.invoice_line_wth_tax_ids.filtered(lambda t: t.is_expenses)))
            #print ('===_compute_amount_wth===',move.amount_tax_wth,move.amount_others)
    
#     @api.one
#     @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
#                  'currency_id', 'company_id', 'invoice_date', 'type')
#     def _compute_amount_wht(self):
        #self.net_pay = self.amount_total - self.amount_wht
        #round_curr = self.currency_id.round
        #self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        #self.amount_tax = sum(line.is_withholding and round_curr(line.amount_total) for line in self.tax_line_ids)
        #self.amount_total = self.amount_untaxed + self.amount_tax
        #self.amount_tax_wth = sum(not line.is_withholding and round_curr(line.amount_total) for line in self.tax_line_ids)#sum(line.amount_wht_line for line in self.invoice_line_ids if line.amount_wht_line)
        
#     @api.multi
#     def finalize_invoice_move_lines(self, move_lines):
#         self.ensure_one()
#         wht_lines = {}
#         for line in self.invoice_line_ids:
#             if line.wht_id:
#                 wht_lines[line.wht_id] = wht_lines.get(line.wht_id, 0.0) + line.amount_wht_line
#         for wht_id in wht_lines.keys():    
#             move_lines.append((0, 0, {
#                                     'name': wht_id.name,
#                                     'credit': wht_lines[wht_id],
#                                     'debit': False,
#                                     'partner_id': self.partner_id.id,
#                                     'account_id': wht_id.account_id.id
#                                     }))
#         for line in move_lines:
#             if line[2].get('move_id') and line[2].get('account_id') == self.account_id.id :
#                 line[2]['credit'] -= sum(wht_lines.values())
#                 
#         return super(account_invoice, self).finalize_invoice_move_lines(move_lines)


    amount_tax_wth = fields.Monetary(string='Withholding Tax',
        store=False, readonly=True, compute='_compute_amount_wth')
    invoice_wth_tax_ids = fields.Many2many('account.tax',
        'account_invoice_wht_tax', 'invoice_id', 'tax_id',
        string='Wth Taxes', domain=[('type_tax_use','!=','none'), ('is_withholding','=',True),'|', ('active', '=', False), ('active', '=', True)])
    # amount_others = fields.Monetary(string='Others')
        #store=False, readonly=True, compute='_compute_amount_wth')
    # invoice_oth_tax_ids = fields.Many2many('account.tax',
    #     'account_invoice_other_tax', 'invoice_id', 'tax_id',
    #     string='Others', domain=[('type_tax_use','!=','none'), ('is_expenses','=',True),'|', ('active', '=', False), ('active', '=', True)])
#         string='Withholding Tax',
#         store=True, readonly=True, compute='_compute_amount_wth', track_visibility='onchange')
#     net_pay = fields.Monetary(string='Net Pay',
#         store=True, readonly=True, compute='_compute_amount_wth', track_visibility='onchange')

    @api.onchange('invoice_wth_tax_ids')#, 'invoice_oth_tax_ids')
    def _onchange_invoice_wth_tax_ids(self):
        # if not self.invoice_wth_tax_ids:
        #     return
        for line in self.invoice_line_ids:
            #line.invoice_line_wth_tax_ids = line._get_computed_taxes_withholding()
            wth_taxes = self.invoice_wth_tax_ids
            # oth_taxes = self.invoice_oth_tax_ids
            #print ('--_onchange_invoice_wth_tax_ids--',taxes)
            if wth_taxes and line.move_id.fiscal_position_id:
                wth_taxes = line.move_id.fiscal_position_id.map_tax(wth_taxes)
            # if oth_taxes and line.move_id.fiscal_position_id:
            #     oth_taxes = line.move_id.fiscal_position_id.map_tax(oth_taxes)
            line.invoice_line_wth_tax_ids = wth_taxes# + oth_taxes
            # if oth_taxes and line.move_id.fiscal_position_id:
            #     wth_taxes += line.move_id.fiscal_position_id.map_tax(oth_taxes)
            # line.invoice_line_wth_tax_ids += wth_taxes
            # line.invoice_line_oth_ids = oth_taxes

    
    # def _inverse_amount_total(self):
    #     for move in self:
    #         if len(move.line_ids) != 2 or move.is_invoice(include_receipts=True):
    #             continue

    #         to_write = []

    #         amount_currency = abs(move.amount_total)
    #         balance = move.currency_id._convert(amount_currency, move.company_currency_id, move.company_id, move.date)

    #         for line in move.line_ids:
    #             if not line.currency_id.is_zero(balance - abs(line.balance)):
    #                 to_write.append((1, line.id, {
    #                     'debit': line.balance > 0.0 and balance or 0.0,
    #                     'credit': line.balance < 0.0 and balance or 0.0,
    #                     'amount_currency': line.balance > 0.0 and amount_currency or -amount_currency,
    #                 }))

    #         move.write({'line_ids': to_write})
            
    # @api.depends('amount_others')#, 'invoice_oth_tax_ids')
    # def _compute_amount(self):
    #     vals = super(AccountMove, self)._compute_amount()
    #     # print ('===s===',vals)
    #     for move in self:
    #         #super(AccountMove, move)._compute_amount()
    #         total = 0.0
    #         total_currency = 0.0
    #         currencies = move._get_lines_onchange_currency().currency_id

    #         for line in move.invoice_line_ids:
    #             if move._payment_state_matters():
    #                 # === Invoices ===

    #                 if not line.exclude_from_invoice_tab:
    #                     # Untaxed amount.
    #                     #total_untaxed += line.balance
    #                     #total_untaxed_currency += line.amount_currency
    #                     total += line.balance
    #                     #total += line.amount_wth_line
    #                     total_currency += line.amount_currency
    #                 elif line.tax_line_id:
    #                     # Tax amount.
    #                     #total_tax += line.balance
    #                     #total_tax_currency += line.amount_currency
    #                     total += line.balance
    #                     #total += line.amount_wth_line
    #                     total_currency += line.amount_currency
    #                 # elif line.account_id.user_type_id.type in ('receivable', 'payable'):
    #                 #     # Residual amount.
    #                 #     total_to_pay += line.balance
    #                 #     total_residual += line.amount_residual
    #                 #     total_residual_currency += line.amount_residual_currency
    #             else:
    #                 # === Miscellaneous journal entry ===
    #                 if line.debit:
    #                     total += line.balance
    #                     #total += line.amount_wth_line
    #                     total_currency += line.amount_currency

    #         total += -move.amount_others
    #         total_currency += -move.amount_others
    #         #print ('====s====',total)
    #         if move.move_type == 'entry' or move.is_outbound():
    #             sign = 1
    #         else:
    #             sign = -1
    #         move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
    #         move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
    #         #print ('=',move.amount_total,move.amount_total_signed,total)
    #     return vals
            
#     def _prepare_tax_line_vals(self, line, tax):
#         vals = super(AccountMove, self)._prepare_tax_line_vals(line=line, tax=tax)
#         print ('==_prepare_tax_line_vals==',tax)
#         vals['is_withholding'] = tax['is_withholding']
#         """ Prepare values to create an account.invoice.tax line
# 
#         The line parameter is an account.invoice.line, and the
#         tax parameter is the output of account.tax.compute_all().
#         """
#         vals = {
#             'move_id': self.id,
#             'name': tax['name'],
#             'tax_id': tax['id'],
#             'amount': tax['amount'],
#             'base': tax['base'],
#             'manual': False,
#             'sequence': tax['sequence'],
#             'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
#             'account_id': self.type in ('out_invoice', 'in_invoice') and (tax['account_id'] or line.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
#             'analytic_tag_ids': tax['analytic'] and line.analytic_tag_ids.ids or False,
#         }
# 
#         # If the taxes generate moves on the same financial account as the invoice line,
#         # propagate the analytic account from the invoice line to the tax line.
#         # This is necessary in situations were (part of) the taxes cannot be reclaimed,
#         # to ensure the tax move is allocated to the proper analytic account.
#         if not vals.get('account_analytic_id') and line.account_analytic_id and vals['account_id'] == line.account_id.id:
#             vals['account_analytic_id'] = line.account_analytic_id.id
#         return vals

    
    # def compute_wth_taxes(self):
    #     """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
    #     account_invoice_tax = self.env['account.invoice.tax']
    #     ctx = dict(self._context)
    #     for invoice in self:
    #         # Delete non-manual tax lines
    #         self._cr.execute("DELETE FROM account_invoice_tax WHERE move_id=%s AND manual is False", (invoice.id,))
    #         if self._cr.rowcount:
    #             self.invalidate_cache()

    #         # Generate one tax line per tax, however many invoice lines it's applied to
    #         tax_grouped = invoice.get_taxes_values()

    #         # Create new tax lines
    #         for tax in tax_grouped.values():
    #             account_invoice_tax.create(tax)

    #     # dummy write on self to trigger recomputations
    #     return self.with_context(ctx).write({'invoice_line_ids': []})
    
# class AccountMoveTax(models.Model):
#     _inherit = "account.invoice.tax"
#     
#     is_withholding = fields.Boolean('Is Withholding Tax', related='tax_id.is_withholding', store=True)
    
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
  
    @api.depends('price_unit', 'discount', 'tax_ids', 'quantity', 'invoice_line_wth_tax_ids', 
                #'invoice_line_oth_ids',
                 'move_id.partner_id', 'move_id.currency_id', 'move_id.company_id',
                 'move_id.invoice_date', 'move_id.date')
    def _compute_price_wth(self):
        for line in self:
            amount_wth_line = 0.0
            # amount_others_line = 0.0
            wth_taxes = line.invoice_line_wth_tax_ids.compute_all(line.price_subtotal, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']
            for tax in wth_taxes:
                amount_wth_line += tax['amount']
            # other_taxes = line.invoice_line_oth_ids.compute_all(line.price_subtotal, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']
            # for oth in other_taxes:
            #     amount_others_line += oth['amount']
            line.amount_wth_line = amount_wth_line
            # line.amount_oth_line = amount_others_line
    
    # @api.depends('invoice_line_wth_tax_ids', 'invoice_line_oth_ids')
    # def _compute_tax_amounts_json(self):
    #     """ Computed field used for custom widget's rendering.
    #         Only set on invoices.
    #     """
    #     for line in self:
    #         # if not move.is_invoice(include_receipts=True):
    #         #     # Non-invoice moves don't support that field (because of multicurrency: all lines of the invoice share the same currency)
    #         #     move.tax_totals_json = None
    #         #     continue

    #         # tax_lines_data = move._prepare_tax_lines_data_for_totals_from_invoice()
            
    #         wth_taxes = line.invoice_line_wth_tax_ids.filtered(lambda t: t.is_withholding).compute_all(line.price_subtotal, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']
    #         # for tax in wth_taxes:
    #         #     amount_wth_line += tax['amount']
    #         other_taxes = line.invoice_line_wth_tax_ids.filtered(lambda t: t.is_expenses).compute_all(line.price_subtotal, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']
    #         # for oth in other_taxes:
    #         #     amount_others_line += oth['amount']

    #         amount_wth_line = sum(tax['amount'] for tax in wth_taxes)
    #         amount_oth_line = sum(tax['amount'] for tax in other_taxes)
    #         #print ('===amount_wth_line=',amount_wth_line,amount_oth_line)
    #         line.tax_amount_json = json.dumps({
    #             'amount_wth_line': amount_wth_line,
    #             'amount_oth_line': amount_oth_line,
    #             #**self._get_tax_totals(move.partner_id, tax_lines_data, move.amount_total, move.amount_untaxed, move.currency_id),
    #             #'allow_tax_edition': move.is_purchase_document(include_receipts=True) and move.state == 'draft',
    #         })

    #wht_id = fields.Many2one('account.tax', string='Wth Tax')
    invoice_line_wth_tax_ids = fields.Many2many('account.tax',
        'account_invoice_line_wht_tax', 'invoice_line_id', 'tax_id',
        string='Wth Taxes', domain=[('type_tax_use','!=','none'), '|', ('active', '=', False), ('active', '=', True)])
    amount_wth_line = fields.Monetary(string='Wth Tax Amount',
        store=False, readonly=True, compute='_compute_price_wth')
    # invoice_line_oth_ids = fields.Many2many('account.tax',
    #     'account_invoice_line_others_tax', 'invoice_line_id', 'tax_id',
    #     string='Others', domain=[('type_tax_use','!=','none'), '|', ('active', '=', False), ('active', '=', True)])
    # amount_oth_line = fields.Monetary(string='Others Amount',
    #     store=False, readonly=True, compute='_compute_price_wth')
    #tax_amount_json = 
    # tax_amount_json = fields.Char(
    #     string="Taxes Totals JSON",
    #     compute='_compute_tax_amounts_json',
    #     readonly=False,
    #     help='Edit Tax amounts if you encounter rounding issues.')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(AccountMoveLine, self)._onchange_product_id()
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            # line.name = line._get_computed_name()
            # line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes_withholding()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(taxes)
            line.invoice_line_wth_tax_ids = taxes
            #line.invoice_line_others_ids 
            # line.product_uom_id = line._get_computed_uom()
            # line.price_unit = line._get_computed_price_unit()
    
    # def _set_taxes(self):
    #     """ Used in on_change to set taxes and price."""
    #     vals = super(AccountMoveLine, self)._set_taxes()
    #     if self.move_id.type in ('out_invoice', 'out_refund'):
    #         if self.move_id.partner_id and self.move_id.partner_id.taxes_wth_id:
    #             #GET TAX FROM PARTNER
    #             wth_taxes = self.move_id.partner_id.taxes_wth_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id) or self.account_id.tax_ids
    #         else:
    #             #GET TAX FROM PRODUCT
    #             wth_taxes = self.product_id.taxes_wth_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id) or self.account_id.tax_ids
    #         #taxes = self.product_id.taxes_id or self.account_id.tax_ids
    #     else:
    #         if self.move_id.partner_id and self.move_id.partner_id.supplier_taxes_wth_id:
    #             #GET TAX FROM PARTNER
    #             wth_taxes = self.move_id.partner_id.supplier_taxes_wth_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id) or self.account_id.tax_ids
    #         else:
    #             #GET TAX FROM PRODUCT
    #             wth_taxes = self.product_id.supplier_taxes_wth_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id) or self.account_id.tax_ids
    #         #taxes = self.product_id.supplier_taxes_id or self.account_id.tax_ids

    #     # Keep only taxes of the company
    #     company_id = self.company_id or self.env.user.company_id
    #     taxes_wth = wth_taxes.filtered(lambda r: r.company_id == company_id)

    #     self.invoice_line_wth_tax_ids = self.move_id.fiscal_position_id.map_tax(taxes_wth, self.product_id, self.move_id.partner_id)
    #     return vals
    

    def _get_computed_taxes_withholding(self):
        self.ensure_one()
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            if self.move_id.partner_id and self.move_id.partner_id.taxes_wth_id:
                wth_taxes = self.partner_id.taxes_wth_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            elif self.product_id.taxes_id:
                wth_taxes = self.product_id.taxes_wth_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            else:
                wth_taxes = self.account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'sale')
            if not wth_taxes and not self.exclude_from_invoice_tab:
                wth_taxes = self.move_id.company_id.account_sale_tax_id
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            if self.move_id.partner_id and self.move_id.partner_id.supplier_taxes_wth_id:
                wth_taxes = self.partner_id.supplier_taxes_wth_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            elif self.product_id.supplier_taxes_id:
                wth_taxes = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
            else:
                wth_taxes = self.account_id.tax_ids.filtered(lambda tax: tax.type_tax_use == 'purchase')
            if not wth_taxes and not self.exclude_from_invoice_tab:
                wth_taxes = self.move_id.company_id.account_purchase_tax_id
        else:
            # Miscellaneous operation.
            wth_taxes = self.account_id.tax_ids

        if self.company_id and wth_taxes:
            wth_taxes = wth_taxes.filtered(lambda tax: tax.company_id == self.company_id)

        return wth_taxes
        

#         fix_price = self.env['account.tax']._fix_tax_included_price
#         if self.move_id.type in ('in_invoice', 'in_refund'):
#             prec = self.env['decimal.precision'].precision_get('Product Price')
#             if not self.price_unit or float_compare(self.price_unit, self.product_id.standard_price, precision_digits=prec) == 0:
#                 self.price_unit = fix_price(self.product_id.standard_price, taxes, fp_taxes)
#                 self._set_currency()
#         else:
#             self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)
#             self._set_currency()
