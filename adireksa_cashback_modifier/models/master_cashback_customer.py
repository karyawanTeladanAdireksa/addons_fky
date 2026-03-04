# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MasterCustomerCashback(models.Model):

    _inherit = "master.customer.cashback"

    cashback_used = fields.Float(
        'Cashback Used',  copy=False, compute="compute_cashback_used")
    cashback_in = fields.Float(
        'Cashback In',  copy=False, compute="compute_cashback_in")

    def compute_cashback_used(self):
    	for rec in self:
            rec.cashback_used = sum([line.value for line in rec.line_ids.filtered(
                lambda x: x.type_id.default_posting == 'credit' and x.type_id.manual_cashback == 'false' and x.state == 'approve')])
            rec.cashback_used += sum([line.value for line in rec.manual_line_ids.filtered(
    		    lambda x: x.type_id.default_posting == 'credit' and x.type_id.manual_cashback == 'true' and x.state == 'approve')])

    def compute_cashback_in(self):
        for rec in self:
            rec.cashback_in = sum([line.value for line in rec.line_ids.filtered(
                lambda x: x.type_id.default_posting == 'debit' and x.state == 'approve')])
            rec.cashback_in += sum([line.value for line in rec.manual_line_ids.filtered(
                lambda x: x.type_id.default_posting == 'debit' and x.state == 'approve')])


class CashbackLines(models.Model):

    _inherit = 'cashback.lines'

    def write(self, vals):
        res = super(CashbackLines, self).write(vals)
        for rec in self:
            if 'state' in vals and vals['state'] == 'approve':
                rec.cashback_id.cashback_in += rec.value
        return res
