# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_calculation_coretax = fields.Char('Tax calculation other', related='company_id.partner_id.tax_calculation_coretax', readonly=False)
    # tax_calculation_coretax = fields.Char(string='Tax calculation other', 
    #     related='company_id.tax_calculation_coretax', default='11/12', readonly=False, store=True)