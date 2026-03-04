# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta
import math
from odoo.tools import float_compare


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    # def assign_outstanding_credit(self, credit_aml_id):
    #     res = super(AccountInvoice, self).assign_outstanding_credit(credit_aml_id)
    #     credit_aml = self.env['account.move.line'].browse(credit_aml_id)
    #     payment = credit_aml.payment_id
    #     if payment:
    #         invoices = payment.invoice_ids.filtered(lambda r: r.type == 'out_invoice')
    #         if invoices:
    #             for invoice in invoices:
    #                 if invoice.residual == 0.0:
    #                     payment.generate_cashback(invoice)
    #     return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    add_cashback_day = fields.Boolean(string='Tambah Keringanan cashback 5 hari', default=False)
    pelunasan_cashback_ids = fields.One2many('payment.cashback.lines', 'payment_id', string='Pelunasan Cashback')
    promo_cashback_id = fields.Many2one('payment.cashback.lines', string='Promo Cashback')

    def generate_cashback(self, invoice):
        cr = self.env.cr
        # Pelunasan Cashback
        cashback_amount = 0.0
        payment_date = datetime.strptime(self.date, '%Y-%m-%d')
        # cr.execute("""SELECT MAX(ap.payment_date) as pdate FROM account_partial_reconcile apr
        #     INNER JOIN account_move_line paml ON paml.id = apr.credit_move_id
        #     inner join account_move_line iaml on iaml.id = apr.debit_move_id 
        #     inner join account_payment ap on ap.id = paml.payment_id 
        #     WHERE iaml.invoice_id = {0} and ap.id != {1}""".format(invoice.id, self.id))
        # rs = cr.dictfetchone()
        # curr_date = datetime.strptime(rs['pdate'] if rs['pdate'] else invoice.date_invoice, '%Y-%m-%d')
        curr_date = datetime.strptime(invoice.invoice_date, '%Y-%m-%d')
        date_diff = abs((payment_date - curr_date).days)
        if self.add_cashback_day:
            date_diff -= 5
        cb = self.env['cashback.rule'].search([('state', '=', 'approve'),
            ('company_id', '=', self.company_id.id)], order='period desc', limit=1)
        # Get correct payment amount
        cr.execute("""SELECT apr.amount as amount FROM account_partial_reconcile apr
            INNER JOIN account_move_line paml ON paml.id = apr.credit_move_id
            INNER JOIN account_move_line iaml ON iaml.id = apr.debit_move_id 
            WHERE iaml.invoice_id = {0} and paml.payment_id = {1}""".format(invoice.id, self.id))
        res = cr.dictfetchone()
        payment_amount = res['amount'] if res['amount'] else 0.0
        for line in cb.line_ids.filtered(lambda r: r.trigger == 'invoice'):
            if date_diff >= line.day1 and date_diff <= line.day2:
                cashback_amount = (line.formula / 100) * payment_amount
                line_id = line.id
        domain = []
        if self.partner_id.category_id:
            domain += [('group_id', 'in', self.partner_id.category_id.ids),('company_id', '=', self.company_id.id)]
            whr = 'and group_id = %d' % (self.partner_id.category_id[0].id)
        else:
            domain += [('partner_id', '=', self.partner_id.id),('company_id', '=', self.company_id.id)]
            whr = 'and partner_id = %d' % (self.partner_id.id)
        mcc_rec = self.env['master.customer.cashback'].search(domain, order='date desc', limit=1)
        if mcc_rec and cashback_amount > 0.0:
            cashback = self.env['payment.cashback.lines'].create({
                'reference': '%s: Pay Invoice Cashback' % (invoice.number),
                'date': self.date, 
                'type_id': self.env.ref('adireksa_cashback_pattern.cashback_pelunasan').id,
                'value': math.ceil(cashback_amount),
                'state': 'waiting_for_approval',
                'cashback_id': mcc_rec.id,
                'payment_id': self.id,
                'invoice_id': invoice.id,
                'cashback_rule_id': line_id,
            })
        # Promo Cashback
        digit_precision = self.env['decimal.accurra']
        if float_compare(invoice.amount_residual) == 0.0:
            cashback_promo_amount = 0.0
            for inv in invoice.invoice_line_ids:
                cr.execute("""SELECT mcp.id, cpl.value FROM master_cashback_product mcp 
                INNER JOIN cashback_product_lines cpl ON cpl.cashback_id = mcp.id
                WHERE mcp.company_id = {0} AND cpl.product_id = {1} {2} and mcp.state = 'confirm'
                and '{3}' between mcp.start_date and mcp.end_date 
                limit 1""".format(self.company_id.id, inv.product_id.id, whr, payment_date))
                res = cr.dictfetchone()
                if res:
                    discount = 0.0
                    if invoice.diskon:
                        for disc in invoice.diskon:
                            discount += disc.formula_diskon 
                    total_discount = inv.price_subtotal * (discount/100) if discount > 0.0 else 0.0
                    cashback_promo_amount += (res['value'] / 100) * (inv.price_subtotal - total_discount)
            if mcc_rec and cashback_promo_amount > 0.0:
                cr.execute("""SELECT id FROM cashback_rule_line WHERE trigger = 'promo' and rule_id = {0} limit 1""".format(cb.id))
                rs = cr.dictfetchone()
                promo_line_id = rs['id'] if rs else False
                cashback = self.env['payment.cashback.lines'].create({
                    'reference': '%s: Product Cashback' % (invoice.name),
                    'date': self.date, 
                    'type_id': self.env.ref('adireksa_cashback_pattern.cashback_pelunasan').id,
                    'value': math.ceil(cashback_promo_amount),
                    'state': 'waiting_for_approval',
                    'cashback_id': mcc_rec.id,
                    'payment_id': self.id,
                    'invoice_id': invoice.id,
                    'cashback_rule_id': promo_line_id,
                })
                self.sudo().write({'promo_cashback_id': cashback.id})


    def action_post(self):
        res = super(AccountPayment, self).post()
        for payment in self:
            invoices = payment.reconciled_invoice_ids.filtered(lambda r: r.move_type == 'out_invoice')
            if invoices:
                for invoice in invoices:
                    payment.generate_cashback(invoice)
        return res


    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()
        for rec in self:
            if rec.pelunasan_cashback_ids:
                if rec.pelunasan_cashback_ids.sudo().filtered(lambda r: r.state == 'approve'):
                    raise UserError("There is an approved cashback for this transaction, you cannot cancel this payment.")
            if rec.promo_cashback_id and rec.promo_cashback_id.state == 'approve':
                raise UserError("There is an approved cashback for this transaction, you cannot cancel this payment.")
            if rec.pelunasan_cashback_ids:
                for p in rec.pelunasan_cashback_ids:
                    p.sudo().unlink()
            if rec.promo_cashback_id and rec.promo_cashback_id.state != 'approve':
                rec.promo_cashback_id.sudo().unlink()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def remove_move_reconcile(self):
        res = super(AccountMoveLine, self).remove_move_reconcile()
        for rec in self:
            rs = rec.payment_id
            if rs:
                if rs.pelunasan_cashback_ids:
                    if rs.pelunasan_cashback_ids.sudo().filtered(lambda r: r.state == 'approve'):
                        raise UserError("There is an approved cashback for this transaction, you cannot cancel this payment.")
                if rs.promo_cashback_id and rs.promo_cashback_id.state == 'approve':
                    raise UserError("There is an approved cashback for this transaction, you cannot cancel this payment.")
                if rs.pelunasan_cashback_ids:
                    for p in rs.pelunasan_cashback_ids:
                        p.sudo().unlink()
                if rs.promo_cashback_id and rs.promo_cashback_id.state != 'approve':
                    rs.promo_cashback_id.sudo().unlink()
        return res
