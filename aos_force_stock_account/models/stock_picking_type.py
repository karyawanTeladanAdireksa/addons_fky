# -*- coding: utf-8 -*- 
# Part of Odoo. See LICENSE file for full copyright and licensing details. 
from odoo import api, fields, models, _
from datetime import datetime 
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare



class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    required_force_account = fields.Boolean('Required Force Account?',default=False)
    default_force_account = fields.Many2one('account.account',
        'Default Force Account', help="Choose the accounting at which you want to value the stock "
            "moves created by the inventory instead of the default one")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    required_force_account = fields.Boolean('Required Force Account?',related="picking_type_id.required_force_account")