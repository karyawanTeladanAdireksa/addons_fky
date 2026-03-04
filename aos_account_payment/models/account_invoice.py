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
    
    @api.depends('other_line_ids', 'other_line_ids.amount')
    def _amount_others(self):
        for move in self:
            move.amount_others = sum([line.amount for line in move.other_line_ids])

    other_line_ids = fields.One2many('account.other.line', 'move_id', string="Other Lines")
    amount_others = fields.Monetary(string='Others', readonly=True,
        compute='_amount_others')

    @api.depends('amount_others')
    def _compute_amount(self):
        vals = super(AccountMove, self)._compute_amount()
        # print ('===s===',vals)
        for move in self:
            #super(AccountMove, move)._compute_amount()
            total = 0.0
            total_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id
            for line in move.line_ids:
                if move._payment_state_matters():
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency
            total += -move.amount_others
            total_currency += -move.amount_others
            #print ('====s====',total,total_currency)
            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            #print ('=',move.amount_total,move.amount_total_signed,total)
        return vals
            
class AccountOtherLine(models.Model):
    _name = 'account.other.line'
    _description = 'Account Others'

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            line.name = line.product_id.name

    name = fields.Char(string='Label', tracking=True, compute='_compute_name', store=True, readonly=False)
    product_id = fields.Many2one('product.product', string="Product", ondelete='restrict')
    #payment_line_id = fields.Many2one('account.payment.line', string='Payment Line', ondelete='restrict')
    move_id = fields.Many2one('account.move', string="Journal Entry", 
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",)
    company_id = fields.Many2one(related='move_id.company_id', store=True, readonly=True)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id),('is_off_balance', '=', False)]",
        check_company=True,
        tracking=True)
    amount = fields.Float(string='Amount', digits='Product Price')

    def _get_account(self, product, fpos, type):
        accounts = product.product_tmpl_id.get_product_accounts(fpos)
        if type == 'out_invoice':
            return accounts['income']
        return accounts['expense']

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        partner = self.move_id.partner_id
        if partner.lang:
            product = product.with_context(lang=partner.lang)
        self.name = product.name

        if product:
            # product = self.env['product.product'].browse(product_id)
            partner = self.move_id.partner_id
            fpos = partner.property_account_position_id
            account = self._get_account(product, fpos, self.move_id.move_type)
            amount = product.standard_price
            # self.name = product.name
            # self.quantity = self.contract_id.plan_id.recurring if self.contract_id.plan_id.duration == 'limited' else 1.0
            self.account_id = account.id
            self.amount = amount

    
    def _prepare_other_line(self, pline):
        vals = {
            'manual': False,
            # 'payment_line_id': pline.id,
            'name': self.name,
            'account_id': self.account_id and self.account_id.id,
            'amount': self.amount,
        }
        return vals