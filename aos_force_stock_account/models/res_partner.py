# -*- coding: utf-8 -*- 
# Part of Odoo. See LICENSE file for full copyright and licensing details. 
from odoo import api, fields, models, _
from datetime import datetime 
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare

class ResPartner(models.Model):
    _inherit = 'res.partner' 
    
    default_account_force_id = fields.Many2one('account.account', company_dependent=True,
        string="Default Force Account",
        domain="[('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=False)