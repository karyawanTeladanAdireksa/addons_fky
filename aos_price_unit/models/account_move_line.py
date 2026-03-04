# -*- coding: utf-8 -*-

from odoo import api, models,fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    price_unit = fields.Monetary(string='Unit Price', digits='Product Price') 