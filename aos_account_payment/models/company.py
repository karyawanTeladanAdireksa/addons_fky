# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning

class ResCompany(models.Model):
    _inherit = "res.company"

    amount_condition = fields.Float('Amount Condition')
    product_meterai_id = fields.Many2one('product.product', string='Meterai')
    