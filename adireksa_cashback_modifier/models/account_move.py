# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoice, self).default_get(fields)
        max_cashback = self.env['ir.config_parameter'].sudo().get_param('customer_cashback.max_cashback')
        res.update({
                'max_cashback': max_cashback
            })
        return res

    cashback_value_type = fields.Selection([('fixed', 'Fixed Value'), ('perc', 'Percentage')], default='fixed', string='Cashback Value Type')
    cashback_per = fields.Float('Cashback %')
    cashback_fixed_value = fields.Float('Cashback Fixed Value')
    cashback_value = fields.Float('Cashback Value', compute='compute_cashback_value')
    cashback_balance = fields.Float('Cashback Balance', compute='compute_cashback_value')
    max_cashback = fields.Float(string='Max Cashback')

    @api.constrains('cashback_per', 'cashback_value_type', 'cashback_fixed_value', 'partner_id')
    def _check_cashback_per(self):
        for rec in self:
            if rec.cashback_balance < rec.cashback_value:
                raise ValidationError(_("Maximum Cashback Allowed are : %s" % (rec.cashback_balance)))
            if rec.cashback_value_type == 'perc' and rec.max_cashback and rec.cashback_per > rec.max_cashback:
                raise ValidationError(_("You cannot set cashback more than max cashback perc!"))
            if rec.cashback_value_type == 'fixed':
                cashback_amount = ((rec.amount_untaxed - rec.discount_amount + rec.amount_tax)* rec.max_cashback)/100.0
                if rec.cashback_fixed_value > cashback_amount:
                    raise ValidationError(_("You cannot set cashback more than max cashback perc!"))

    @api.depends('cashback_per', 'amount_untaxed', 'discount_amount', 'amount_tax', 'cashback_value_type', 'cashback_fixed_value', 'partner_id')
    def compute_cashback_value(self):
        for rec in self:
            rec.cashback_value = 0.0
            rec.cashback_balance = 0.0
            if rec.cashback_value_type == 'perc':
                rec.cashback_value = ((rec.amount_untaxed - rec.discount_amount + rec.amount_tax)* rec.cashback_per)/100.0
            if rec.cashback_value_type == 'fixed':
                rec.cashback_value = rec.cashback_fixed_value
            if rec.partner_id:
                domain = []
                if rec.partner_id.category_id:
                    domain += [('group_id', 'in', rec.partner_id.category_id.ids)]
                else:
                    domain += [('partner_id', '=', rec.partner_id.id)]
                mcc_rec = self.env['master.customer.cashback'].search(domain, limit=1)
                rec.cashback_balance = mcc_rec.balance
                
                

    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        domain = []
        for move in self:
            if move.partner_id.category_id:
                domain += [('group_id', 'in', move.partner_id.category_id.ids)]
            else:
                domain += [('partner_id', '=', move.partner_id.id)]
            mcc_rec = move.env['master.customer.cashback'].search(domain, limit=1)
            type_out = move.env['cashback.type'].search([('id', '=', move.env.ref('customer_cashback.cashback_type_ci').id)])
            if mcc_rec and move.cashback_value > 0:
                move.env['cashback.lines'].create({'name': move.name,
                            'partner_id' : move.partner_id.id,
                            'date': move.date_invoice, 
                            'type_id': type_out.id,
                            'value': move.cashback_value,
                            'reference': move.ref,
                            'state': 'approve',
                            'cashback_id': mcc_rec.id})
        return res
    
    def action_cancel(self):
        for rec in self:
            domain = []
            if rec.partner_id.category_id:
                domain += [('group_id', 'in', rec.partner_id.category_id.ids)]
            else:
                domain += [('partner_id', '=', rec.partner_id.id)]
            mcc_rec = self.env['master.customer.cashback'].search(domain, limit=1)
            if mcc_rec:
                lines = self.env['cashback.lines'].search([('cashback_id', '=', mcc_rec.id),
                                                           ('name', '=', rec.number)])
                if lines:
                    lines.unlink()
        return super(AccountInvoice, self).action_cancel()

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'diskon',
        'discount_amount', 
        'cashback_value_type', 
        'cashback_per', 
        'cashback_fixed_value')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for move in self:
            cashback_amt = amount_tax = amount_untaxed = total = total_currency = 0.0
            percent = move.cashback_per
            amount_total_b_cashback = total_currency - move.discount_amount
            if move.cashback_value_type == 'perc':
                cashback_amt = amount_total_b_cashback - (amount_total_b_cashback * (1 - (percent or 0.0) / 100.0))
            if move.cashback_value_type == 'fixed':
                cashback_amt = move.cashback_fixed_value

            move.cashback_value = cashback_amt
            move.amount_total = move.amount_total - move.discount_amount - cashback_amt


    # 
    # def compute_invoice_totals(self, company_currency, invoice_move_lines):
    #     if self.cashback_value:
    #         cashback = self.cashback_value or 0.0
    #         for line in invoice_move_lines:
    #             line['price'] -= cashback
    #             break
    #     return super(AccountInvoice, self).compute_invoice_totals(company_currency, invoice_move_lines)