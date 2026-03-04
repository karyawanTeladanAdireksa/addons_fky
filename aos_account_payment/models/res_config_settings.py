# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    amount_condition = fields.Float('Amount Condition &gt;=', related='company_id.amount_condition', readonly=False)
    product_meterai_id = fields.Many2one('product.product', string='Meterai', related='company_id.product_meterai_id', readonly=False)
    
