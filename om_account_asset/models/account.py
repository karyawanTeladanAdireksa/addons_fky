# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    create_asset = fields.Selection([('no', 'No'), 
                                    ('draft', 'Create in draft'), 
                                    ('validate', 'Create and validate')],
                                    required=True, default='no', tracking=True)
    asset_category_id = fields.Many2one('account.asset.category', string='Category', help='Setup Category per account if not take from account.move.line')
    asset_type = fields.Selection([('purchase', 'Fixed Asset'), ('sale', 'Deferred Revenue'), ('expense', 'Prepaid Expense')],
                            required=True, index=True, default='purchase')
    multiple_assets_per_line = fields.Boolean(string='Multiple Assets per Line', default=False, tracking=True,
        help="Multiple asset items will be generated depending on the bill line quantity instead of 1 global asset.")
