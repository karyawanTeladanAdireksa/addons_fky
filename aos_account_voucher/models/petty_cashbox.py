# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _

class PettyCashbox(models.Model):
    _name = 'petty.cashbox'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Petty Cash'

    @api.depends('cashbox_lines_ids', 'cashbox_lines_ids.coin_value', 'cashbox_lines_ids.number')
    def _compute_total(self):
        for cashbox in self:
            cashbox.total_coins = sum([line.subtotal for line in cashbox.cashbox_lines_ids.filtered(lambda c: c.type == 'coins')])
            cashbox.total_paper = sum([line.subtotal for line in cashbox.cashbox_lines_ids.filtered(lambda c: c.type == 'paper')])
            cashbox.total = sum([line.subtotal for line in cashbox.cashbox_lines_ids])

    name = fields.Char('Description', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Date', default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', string="Journal", readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', related='journal_id.currency_id')
    cashbox_lines_ids = fields.One2many('petty.cashbox.line', 'cashbox_id', string="Petty Cash", readonly=True, states={'draft': [('readonly', False)]})
    total_coins = fields.Float(string='Coins', compute='_compute_total', store=True)
    total_paper = fields.Float(string='Paper',compute='_compute_total', store=True)
    total = fields.Float(compute='_compute_total', store=True)
    state = fields.Selection([('draft','Draft'),('posted','Posted')], string='State', default='draft', readonly=True)
    
    def _prepare_petty_cash_line(self):
        paper_ranges = [100000, 75000, 50000, 20000, 10000, 5000, 2000, 1000]
        coin_ranges = [1000, 500, 200, 100]
        values = []
        for paper in paper_ranges:
            vals = {}
            vals['type'] = 'paper'
            vals['coin_value'] = paper
            vals['cashbox_id'] = self.id
            values.append(vals)
        for coin in coin_ranges:
            vals = {}
            vals['type'] = 'coins'
            vals['coin_value'] = coin
            vals['cashbox_id'] = self.id
            values.append(vals)
        #print ('===_prepare_petty_cash_line==',values)
        return values

    def action_compute(self):
        self.cashbox_lines_ids.unlink()
        self.env['petty.cashbox.line'].create(self._prepare_petty_cash_line())

    def action_post(self):
        for cash in self:
            cash.state = 'posted'

    def action_cancel_draft(self):
        for cash in self:
            cash.state = 'draft'


class PettyCashboxLine(models.Model):
    _name = 'petty.cashbox.line'
    _description = 'Petty Cash Line'

    @api.depends('coin_value', 'number')
    def _sub_total(self):
        """ Calculates Sub total"""
        for cashbox_line in self:
            cashbox_line.subtotal = cashbox_line.coin_value * cashbox_line.number

    cashbox_id = fields.Many2one('petty.cashbox', string='Petty Cash')
    date = fields.Date('Date', related='cashbox_id.date', store=True)
    type = fields.Selection([('coins','Coins'),('paper','Paper')], string="Type")
    coin_value = fields.Float(string='Coin/Bill Value', required=True, digits=0, default=0)
    number = fields.Integer(string='#Coins/Bills', help='Opening Unit Numbers')
    subtotal = fields.Float(compute='_sub_total', string='Subtotal', digits=0, readonly=True, store=True)
    journal_id = fields.Many2one('account.journal', string="Journal", related='cashbox_id.journal_id', store=True)
    currency_id = fields.Many2one('res.currency', related='cashbox_id.currency_id', store=True)
    state = fields.Selection([('draft','Draft'),('posted','Posted')], related='cashbox_id.state', store=True)


    # @api.depends('start_bank_stmt_ids', 'end_bank_stmt_ids')
    # def _compute_currency(self):
    #     for cashbox in self:
    #         cashbox.currency_id = False
    #         if cashbox.end_bank_stmt_ids:
    #             cashbox.currency_id = cashbox.end_bank_stmt_ids[0].currency_id
    #         if cashbox.start_bank_stmt_ids:
    #             cashbox.currency_id = cashbox.start_bank_stmt_ids[0].currency_id