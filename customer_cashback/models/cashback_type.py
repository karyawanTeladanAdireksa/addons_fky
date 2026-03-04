# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CashbackType(models.Model):

    _name = 'cashback.type'
    _inherit = ['mail.thread']
    _description = 'Cashback Type'

    name = fields.Char('Name', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, tracking=True)
    manual_cashback = fields.Selection([('true', 'True'), ('false', 'False')], 'Manual Cashback', default="false", tracking=True)
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'Default Posting', default="debit", tracking=True)

    def write(self, vals):
        name_list = ('Sales Order (In)', 'Sales Order (Out)', 'Customer Invoice')
        if self.name in name_list and 'name' in vals:
            raise UserError(_("You can't change!"))
        return super(CashbackType, self).write(vals)