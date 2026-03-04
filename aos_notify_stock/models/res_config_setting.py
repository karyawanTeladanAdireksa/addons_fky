# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    batas_atas = fields.Integer(string="Batas Atas QTY", default=20,config_parameter='aos_notify_stock.batas_atas')
    batas_bawah = fields.Integer(string="Batas Bawah QTY", default=20 ,config_parameter='aos_notify_stock.batas_bawah')
    