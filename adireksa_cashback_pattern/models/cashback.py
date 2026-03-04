# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta


class MasterCustomerCashback(models.Model):
    _inherit = 'master.customer.cashback'

    cashback_type = fields.Selection([('group', 'Customer Group'), ('customer', 'Customer')], 
        default='group', string='Cashback Type')
    automatic_line_ids = fields.One2many('automatic.cashback.lines', 'cashback_id', string='Automatic Cashback')
    paid_line_ids = fields.One2many('payment.cashback.lines', 'cashback_id', string='Cashback Rule')

    def compute_cashback_used(self):
        res = super(MasterCustomerCashback, self).compute_cashback_used()
        for rec in self:
            rec.cashback_used += sum([line.value for line in rec.automatic_line_ids.filtered(
                lambda x: x.type_id.default_posting == 'credit' and x.state == 'approve')])
            rec.cashback_used += sum([line.value for line in rec.paid_line_ids.filtered(
                lambda x: x.type_id.default_posting == 'credit' and x.state == 'approve')])
        return res

    def compute_cashback_in(self):
        res = super(MasterCustomerCashback, self).compute_cashback_in()
        for rec in self:
            rec.cashback_in += sum([line.value for line in rec.automatic_line_ids.filtered(
                lambda x: x.type_id.default_posting == 'debit' and x.state == 'approve')])
            rec.cashback_in += sum([line.value for line in rec.paid_line_ids.filtered(
                lambda x: x.type_id.default_posting == 'debit' and x.state == 'approve')])
        return res

    def print_cashback_report(self):
        view = self.env.ref('adireksa_cashback_pattern.cashback_print_view')
        return {
            'name': _('Print Cashback Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cashback.print',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
        }


class MasterCashbackProduct(models.Model):
    _inherit = 'master.cashback.product'

    cashback_type = fields.Selection([('group', 'Customer Group'), ('customer', 'Customer')], 
        default='group', string='Cashback Type')


class AutomaticCashbackLines(models.Model):
    _name = 'automatic.cashback.lines'
    _description = 'Automatic Cashback Lines'

    name = fields.Char(string='Name')
    date = fields.Date('Date')
    type_id = fields.Many2one('cashback.type', 'Type')
    default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), (
        'approve', 'Approve')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback')
    value = fields.Float('Value')
    cashback_rule_id = fields.Many2many('cashback.rule.line', 'automatic_cashback_rule_rel', string='Cashback Rule')

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True


class PaymentCashbackLines(models.Model):
    _name = 'payment.cashback.lines'
    _description = 'Payment Cashback Lines'

    date = fields.Date('Date')
    type_id = fields.Many2one('cashback.type', 'Type')
    default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), (
        'approve', 'Approve')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback')
    value = fields.Float('Value')
    payment_id = fields.Many2one('account.payment', string='Payment Receipt')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    cashback_rule_id = fields.Many2one('cashback.rule.line', string='Cashback Rule')
    amount_total = fields.Float(string='Nilai Nota', compute='_compute_total', default=0.0)
    total_day = fields.Integer(string='Days', compute='_compute_total', default=0)

    def _compute_total(self):
        cr = self.env.cr
        for rec in self:
            cr.execute("""SELECT apr.amount as amount, paml.date
                FROM account_partial_reconcile apr
                INNER JOIN account_move_line paml ON paml.id = apr.credit_move_id
                INNER JOIN account_move_line iaml ON iaml.id = apr.debit_move_id 
                WHERE iaml.move_id = {0} and paml.payment_id = {1}""".format(rec.invoice_id.id, rec.payment_id.id))
            res = cr.dictfetchone()
            payment_amount = res['amount'] if res['amount'] else 0.0
            pdate = res['date'] if res['date'] else False
            if pdate:
                payment_date = datetime.strptime(str(pdate), '%Y-%m-%d')
                curr_date = datetime.strptime(str(rec.invoice_id.invoice_date), '%Y-%m-%d')
                date_diff = abs((payment_date - curr_date).days)
            else:
                date_diff = 0
            rec.amount_total = payment_amount
            rec.total_day = date_diff

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True
