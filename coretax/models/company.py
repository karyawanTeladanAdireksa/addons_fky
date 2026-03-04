# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    tax_calculation_coretax = fields.Char(string='Tax calculation other', default='11/12')
    