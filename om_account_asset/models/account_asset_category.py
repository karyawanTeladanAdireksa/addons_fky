# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class AccountAssetCategory(models.Model):
    _name = 'account.asset.category'
    _description = 'Asset category'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, index=True, string="Asset Type")
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tag')
    account_asset_id = fields.Many2one('account.account', string='Asset Account',
                            required=False,
                            domain=[('internal_type','=','other'), ('deprecated', '=', False)],
                            help="Account used to record the purchase of the asset at its original price.")
    account_depreciation_id = fields.Many2one('account.account',
                            string='Accum Depr. Account',
                            required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)],
                            help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id = fields.Many2one('account.account',
                            string='Expense Account',
                            required=True,
                            domain=[('internal_type','=','other'), ('deprecated', '=', False)],
                            help="Account used in the periodical entries,"
                                " to record a part of the asset as expense.")
    account_depreciation_disposal_id = fields.Many2one('account.account',
                            string='Sell/Disposal Account',
                            required=False,
                            domain=[('internal_type','=','other'), ('deprecated', '=', False)],
                            help="Account used in the periodical entries,"
                                " to record a part of the asset as expense.")
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.asset.category'))
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')],
                              string='Computation Method', required=True, default='linear',
        help="Choose the method to use to compute the amount of depreciation lines.\n"
            "  * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n"
            "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    method_number = fields.Integer(string='Number of Depreciations', default=12,
                                   help="The number of depreciations needed to depreciate your asset")
    method_period = fields.Integer(string='Period Length', default=1,
                                   help="State here the time between 2 depreciations, in months", required=True)
    method_progress_factor = fields.Float('Degressive Factor', default=0.3)
    method_time = fields.Selection([('number', 'Number of Entries'), ('end', 'Ending Date')],
                                   string='Time Method', required=True, default='number',
        help="Choose the method to use to compute the dates and number of entries.\n"
           "  * Number of Entries: Fix the number of entries and the time between 2 depreciations.\n"
           "  * Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond.")
    method_end = fields.Date('Ending date')
    prorata = fields.Boolean(string='Prorata Temporis',
                             help='Indicates that the first depreciation entry for this asset have to be done from the '
                                  'purchase date instead of the first of January')
    open_asset = fields.Boolean(string='Auto-Confirm Assets',
                                help="Check this if you want to automatically confirm the assets "
                                     "of this category when created by invoices.")
    group_entries = fields.Boolean(string='Group Journal Entries',
                                   help="Check this if you want to group the generated entries by categories.")
    asset_type = fields.Selection([('purchase', 'Fixed Asset'), ('sale', 'Deferred Revenue'), ('expense', 'Prepaid Expense')],
                            required=True, index=True, default='purchase')
    #original_move_line_ids = fields.Many2many('account.move.line', 'asset_asset_move_line_rel', 'asset_id', 'line_id', string='Journal Items', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    day_range = fields.Integer(default=15)
    date_first_depreciation = fields.Selection([
        ('last_curr_period', 'Last Current Month'),
        ('last_next_period', 'Last Next Month'),
        ('manual', 'Manual (Defaulted on Purchase Date)')],
        string='Depreciation Dates', default='last_next_period', required=True,
        help='The way to compute the date of the first depreciation.\n'
             '  * Based on last day of purchase period: The depreciation dates will'
             ' be based on the last day of the purchase month or the purchase'
             ' year (depending on the periodicity of the depreciations).\n'
             '  * Based on purchase date: The depreciation dates will be based on the purchase date.')

    @api.onchange('account_asset_id')
    def onchange_account_asset(self):
        if self.asset_type == "purchase":
            self.account_depreciation_id = self.account_asset_id
        elif self.asset_type == "sale":
            self.account_depreciation_expense_id = self.account_asset_id

    @api.onchange('asset_type')
    def onchange_type(self):
        if self.asset_type == 'sale':
            self.prorata = True
            self.method_period = 1
        else:
            self.method_period = 12

    @api.onchange('method_time')
    def _onchange_method_time(self):
        if self.method_time != 'number':
            self.prorata = False

