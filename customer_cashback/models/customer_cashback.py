# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MasterCustomerCashback(models.Model):

    _name = "master.customer.cashback"
    _description = "Master Customer Cashback"

    name = fields.Char(string='Number', required=True, copy=False,
                       readonly=True, index=True, default=lambda self: _('New'))
    cashback_name = fields.Char(string='Cashback Name')
    date = fields.Date()
    cashback_type = fields.Selection([('group', 'Customer Group'), (
        'customer', 'Customer')], default='customer', string='Cashback Type')
    partner_id = fields.Many2one('res.partner', string='Customer')
    group_id = fields.Many2one('customer.group', string='Customer Group')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')],
                             default='draft', string='Status', readonly=True, copy=False, index=True)
    account_id = fields.Many2one('account.account', string='Cashback Account')
    expense_account_id = fields.Many2one(
        'account.account', string='Cashback Expense Account')
    cashback_in = fields.Float('Cashback In', copy=False)
    cashback_used = fields.Float('Cashback Used',  copy=False)
    balance = fields.Float('Balance', compute='compute_cashback_balance')
    journal_id = fields.Many2one('account.journal', 'Journal')
    line_ids = fields.One2many(
        'cashback.lines', 'cashback_id', 'Cashback Summary')
    manual_line_ids = fields.One2many(
        'manual.cashback.lines', 'cashback_id', 'Manual Cashback')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    cashback_pending = fields.Float(
        'Cashback Pending', compute="compute_cashback_pending")
    cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), (
        'customer_invoice', 'Customer Invoice')], related="company_id.cashback_deduction_option", string="Cashback Deduction Option")

    @api.depends('cashback_in', 'cashback_used', 'cashback_pending')
    def compute_cashback_balance(self):
        for rec in self:
            rec.balance = rec.cashback_in - rec.cashback_used

    @api.depends('line_ids.value', 'line_ids.state')
    def compute_cashback_pending(self):
        for rec in self:
            rec.cashback_pending = sum(
                [line.value for line in rec.line_ids.filtered(lambda x: x.state == 'pending')])

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'master.customer.cashback') or _('New')
        return super(MasterCustomerCashback, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'confirm'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True


class CashbackLines(models.Model):

    _name = 'cashback.lines'
    _description = 'Cashback Lines'

    name = fields.Char('Transaction Number')
    partner_id = fields.Many2one('res.partner', 'Customer')
    date = fields.Date('Transaction Date')
    type_id = fields.Many2one('cashback.type', 'Type')
    default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    value = fields.Float()
    reference = fields.Char()
    cashback_id = fields.Many2one('master.customer.cashback')
    state = fields.Selection([('pending', 'Pending'), ('approve', 'Approve')],
                             default='pending', string='Status', readonly=True, copy=False, index=True)


class ManualCashbackLines(models.Model):

    _name = 'manual.cashback.lines'
    _description = 'Manual Cashback Lines'

    date = fields.Date('Date')
    type_id = fields.Many2one('cashback.type', 'Type')
    default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), (
        'approve', 'Approve')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback')
    line_ids = fields.One2many(
        'manual.cashback.so.lines', 'manual_cashback_id')

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    real_omset = fields.Float('Real Omset')
    total_omset = fields.Float('Total Omset')
    final_omset = fields.Float('Final Omset')
    cashback = fields.Float('Cashback %')
    value = fields.Float('Value')
    cashback_calculation = fields.Boolean('Cashback Calculation')

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True


class ManualCashbackSoLines(models.TransientModel):

    _name = 'manual.cashback.so.lines'
    _description = 'Manual Cashback SO Lines'

    so_id = fields.Many2one('sale.order', 'SO Number')
    so_date = fields.Date('SO Date')
    so_value = fields.Float('SO Value')
    manual_cashback_id = fields.Many2one('manual.cashback.lines')
