# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class AccountAssetAsset(models.Model):
    _name = 'account.asset.asset'
    _description = 'Asset/Revenue Recognition'
    _inherit = ['mail.thread']

    # entry_count = fields.Integer(compute='_entry_count', string='# Asset Entries')
    # depr_line_count = fields.Integer(compute='_entry_count', string='# Asset Depr.')
    name = fields.Char(string='Asset Name', required=True,
                       readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char(string='Reference', size=32, readonly=True, default='/',
                       states={'draft': [('readonly', False)]})
    value = fields.Float(string='Gross Value', required=True, readonly=True,
                         digits=0, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.asset.asset'))
    note = fields.Text()
    category_id = fields.Many2one('account.asset.category', string='Category',
                                  required=True, change_default=True,
                                  readonly=True, states={'draft': [('readonly', False)]})
    # account_depreciation_id = fields.Many2one('account.account',
    #                             string='Accum Depr. Account',
    #                             required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)],
    #                             help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id = fields.Many2one('account.account',
                                string='Expense Account',
                                required=False,
                                domain=[('internal_type','=','other'), ('deprecated', '=', False)],
                                help="Account used in the periodical entries,"
                                    " to record a part of the asset as expense.")
    date = fields.Date(string='Date', required=True, readonly=True,
                       states={'draft': [('readonly', False)]}, default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Draft'), ('open', 'Running'), ('close', 'Close')],
                             'Status', required=True, copy=False, default='draft',
        help="When an asset is created, the status is 'Draft'.\n"
            "If the asset is confirmed, the status goes in 'Running' and the depreciation "
             "lines can be posted in the accounting.\n"
            "You can manually close an asset when the depreciation is over. If the last line"
             " of depreciation is posted, the asset automatically goes in that status.")
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 readonly=True, states={'draft': [('readonly', False)]})
    method = fields.Selection([('linear', 'Linear'), ('degressive', 'Degressive')],
                              string='Computation Method', required=True, readonly=True,
                              states={'draft': [('readonly', False)]}, default='linear',
        help="Choose the method to use to compute the amount of depreciation lines.\n  * Linear:"
             " Calculated on basis of: Gross Value / Number of Depreciations\n"
            "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor")
    method_number = fields.Integer(string='Number of Depreciations', readonly=True,
                                   states={'draft': [('readonly', False)]}, default=12,
                                   help="The number of depreciations needed to depreciate your asset")
    method_period = fields.Integer(string='Number of Months in a Period', required=True,
                                   readonly=True, default=1, states={'draft': [('readonly', False)]},
        help="The amount of time between two depreciations, in months")
    method_end = fields.Date(string='Ending Date', readonly=True, states={'draft': [('readonly', False)]})
    method_progress_factor = fields.Float(string='Degressive Factor',
                                          readonly=True, default=0.3, states={'draft': [('readonly', False)]})
    value_residual = fields.Float(compute='_amount_residual', digits=0, string='Residual Value')
    method_time = fields.Selection([('number', 'Number of Entries'), ('end', 'Ending Date')],
                                   string='Time Method', required=True, readonly=True, default='number',
                                   states={'draft': [('readonly', False)]},
        help="Choose the method to use to compute the dates and number of entries.\n"
             "  * Number of Entries: Fix the number of entries and the time between 2 depreciations.\n"
             "  * Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond.")
    prorata = fields.Boolean(string='Prorata Temporis', readonly=True, states={'draft': [('readonly', False)]},
        help='Indicates that the first depreciation entry for this asset'
             ' have to be done from the asset date (purchase date) '
             'instead of the first January / Start date of fiscal year')
    depreciation_line_ids = fields.One2many('account.asset.depreciation.line', 'asset_id',
                                            string='Depreciation Lines', readonly=True,
                                            states={'draft': [('readonly', False)], 'open': [('readonly', False)]})
    salvage_value = fields.Float(string='Salvage Value', digits=0, readonly=True,
                                 states={'draft': [('readonly', False)]},
        help="It is the amount you plan to have that you cannot depreciate.")
    invoice_id = fields.Many2one('account.move', string='Journal Entries', states={'draft': [('readonly', False)]}, copy=False)
    asset_type = fields.Selection(related="category_id.asset_type", string='Type', store=True)
    day_range = fields.Integer(related="category_id.day_range", string='Day Range', default=15)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tag')
    date_first_depreciation = fields.Selection([
        ('last_curr_period', 'Last Current Month'),
        ('last_next_period', 'Last Next Month'),
        ('manual', 'Manual'),],
        string='Depreciation Dates', default='last_next_period',
        readonly=True, states={'draft': [('readonly', False)]}, required=True,
        help='The way to compute the date of the first depreciation.\n'
             '  * Based on last day of purchase period: The depreciation'
             ' dates will be based on the last day of the purchase month or the '
             'purchase year (depending on the periodicity of the depreciations).\n'
             '  * Based on purchase date: The depreciation dates will be based on the purchase date.\n')
    first_depreciation_manual_date = fields.Date(
        string='First Depreciation Date',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Note that this date does not alter the computation of the first '
             'journal entry in case of prorata temporis assets. It simply changes its accounting date'
    )
    #value_monthly = fields.Integer(compute='_amount_residual', digits=0, string='Monthly Depreciation')
    # depreciation_number = fields.Float(compute='_amount_residual', digits=0, string='Number of Depreciated')
    # depreciation_amount = fields.Float(compute='_amount_residual', digits=0, string='Amount of Depreciated')
    # Capital gain
    parent_id = fields.Many2one('account.asset.asset', help="An asset has a parent when it is the result of gaining value")
    children_ids = fields.One2many('account.asset.asset', 'parent_id', help="The children are the gains in value of this asset")
    original_move_line_ids = fields.Many2many('account.move.line', 'asset_asset_move_line_rel', 'asset_id', 'line_id', string='Journal Items', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    depreciation_move_ids = fields.One2many('account.move', 'asset_id', string='Depreciation Lines', readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)], 'paused': [('readonly', False)]})
    
    depreciation_monthly_value = fields.Float(compute='_entry_count', string='Monthly Depreciation')
    depreciation_entries_count = fields.Integer(compute='_entry_count', string='# Posted Depreciation Entries')
    depreciation_residual_count = fields.Integer(compute='_entry_count', string='# Residual Depreciation Count')
    depreciation_entries_value = fields.Float(compute='_entry_count', string='Amount Posted Depreciation Entries')
    gross_increase_count = fields.Integer(compute='_entry_count', string='# Gross Increases', help="Number of assets made to increase the value of the asset")
    total_depreciation_entries_count = fields.Integer(compute='_entry_count', string='# Depreciation Entries', help="Number of depreciation entries (posted or not)")

    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for ct in self:
            name = ct.name
            if ct.code:
                name += ' (' + ct.code + ')'
            result.append((ct.id, name))
        return result

    @api.onchange('date')
    def _onchange_date(self):
        for record in self.filtered(lambda a: a.day_range != 0):
            if record.date.day < record.day_range:
                record.date_first_depreciation = 'last_curr_period'
            elif record.date.day >= record.day_range:
                record.date_first_depreciation = 'last_next_period'
            else:
                record.date_first_depreciation = 'manual'

    @api.model
    def _get_views(self, type):
        form_view = self.env.ref('om_account_asset.view_account_asset_asset_form')
        tree_view = self.env.ref('om_account_asset.view_account_asset_asset_purchase_tree')
        if type == 'sale':
            form_view = self.env.ref('om_account_asset.view_account_asset_asset_revenue_form')
            tree_view = self.env.ref('om_account_asset.view_account_asset_asset_sale_tree')
        elif type == 'expense':
            form_view = self.env.ref('om_account_asset.view_account_asset_asset_expense_form')
            tree_view = self.env.ref('om_account_asset.view_account_asset_asset_expense_tree')
        return [[tree_view.id, "tree"], [form_view.id, "form"]]

    @api.onchange('original_move_line_ids', 'original_move_line_ids.account_id', 'asset_type')
    def _onchange_original_move_line(self):
        for record in self:
            #misc_journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('company_id', '=', record.company_id.id)], limit=1)
            if not record.original_move_line_ids:
                record.value = record.value or False
                continue
            if any(line.move_id.state == 'draft' for line in record.original_move_line_ids):
                raise UserError(_("All the lines should be posted"))
            if any(type != record.original_move_line_ids[0].move_id.move_type for type in record.original_move_line_ids.mapped('move_id.move_type')):
                raise UserError(_("All the lines should be from the same move type"))
            #print ('===record==',record)
            # if not record.category_id.journal_id:
            #     record.journal_id = misc_journal_id
            total_credit = sum(line.credit for line in record.original_move_line_ids)
            total_debit = sum(line.debit for line in record.original_move_line_ids)
            record.value = total_credit + total_debit
            if record.category_id.account_asset_id.multiple_assets_per_line and len(record.original_move_line_ids) == 1:
                record.value /= max(1, int(record.original_move_line_ids.quantity))
            if (total_credit and total_debit) or record.value == 0:
                raise UserError(_("You cannot create an asset from lines containing credit and debit on the account or with a null amount"))

    @api.depends('method_number', 'depreciation_line_ids.move_posted_check', 'depreciation_line_ids.move_id', 'depreciation_line_ids.move_id.state')
    def _entry_count(self):
        for asset in self:
            asset.depreciation_entries_count = len(asset.depreciation_line_ids.filtered(lambda dl: dl.move_id and dl.move_id.state == 'posted')) or 0 #TOTAL DEPRE LINE POSTED / CLOSED
            asset.depreciation_residual_count = asset.method_number - asset.depreciation_entries_count
            asset.depreciation_entries_value = sum([line.amount for line in asset.depreciation_line_ids.filtered(lambda al: al.move_id or al.closed)]) or 0 #TOTAL AMOUNT YG SUDAH TERDEPRE
            asset.depreciation_monthly_value = asset.value_residual / (asset.method_number or 1) #RATA DEPRE PER BULAN
            asset.total_depreciation_entries_count = len(asset.depreciation_line_ids) #TOTAL DEPRE YANG AKAN TERGENERATE
            asset.gross_increase_count = len(asset.children_ids) 

    def unlink(self):
        for asset in self:
            if asset.state in ['open', 'close']:
                raise UserError(_('You cannot delete a document that is in %s state.') % (asset.state,))
            for depreciation_line in asset.depreciation_line_ids:
                if depreciation_line.move_id:
                    raise UserError(_('You cannot delete a document that contains posted entries.'))
        return super(AccountAssetAsset, self).unlink()

    @api.model
    def _cron_generate_entries(self):
        self.compute_generated_entries(datetime.today())

    @api.model
    def compute_generated_entries(self, date, asset_type=None):
        # Entries generated : one by grouped category and one by asset from ungrouped category
        created_move_ids = []
        type_domain = []
        if asset_type:
            type_domain = [('type', '=', asset_type)]

        ungrouped_assets = self.env['account.asset.asset'].search(type_domain + [('state', '=', 'open'), ('category_id.group_entries', '=', False)])
        created_move_ids += ungrouped_assets._compute_entries(date, group_entries=False)

        for grouped_category in self.env['account.asset.category'].search(type_domain + [('group_entries', '=', True)]):
            assets = self.env['account.asset.asset'].search([('state', '=', 'open'), ('category_id', '=', grouped_category.id)])
            created_move_ids += assets._compute_entries(date, group_entries=True)
        return created_move_ids

    def _compute_board_amount(self, sequence, residual_amount, amount_to_depr,
                              undone_dotation_number, posted_depreciation_line_ids,
                              total_days, depreciation_date):
        amount = 0
        if sequence == undone_dotation_number:
            amount = residual_amount
        else:
            if self.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                if self.prorata:
                    amount = amount_to_depr / self.method_number
                    if sequence == 1:
                        date = self.date
                        if self.method_period % 12 != 0:
                            month_days = calendar.monthrange(date.year, date.month)[1]
                            days = month_days - date.day + 1
                            amount = (amount_to_depr / self.method_number) / month_days * days
                        else:
                            days = (self.company_id.compute_fiscalyear_dates(date)['date_to'] - date).days + 1
                            amount = (amount_to_depr / self.method_number) / total_days * days
            elif self.method == 'degressive':
                amount = residual_amount * self.method_progress_factor
                if self.prorata:
                    if sequence == 1:
                        date = self.date
                        if self.method_period % 12 != 0:
                            month_days = calendar.monthrange(date.year, date.month)[1]
                            days = month_days - date.day + 1
                            amount = (residual_amount * self.method_progress_factor) / month_days * days
                        else:
                            days = (self.company_id.compute_fiscalyear_dates(date)['date_to'] - date).days + 1
                            amount = (residual_amount * self.method_progress_factor) / total_days * days
        return amount

    def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
        undone_dotation_number = self.method_number
        if self.method_time == 'end':
            end_date = self.method_end
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = date(depreciation_date.year, depreciation_date.month,
                                         depreciation_date.day) + relativedelta(months=+self.method_period)
                undone_dotation_number += 1
        if self.prorata:
            undone_dotation_number += 1
        return undone_dotation_number

    def _get_purchase_date(self):
        #self.date_purchase + relativedelta(months=-self.method_period)
        return {}

    def compute_depreciation_board(self):
        self.ensure_one()

        posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual
            purchase_date = self._get_purchase_date()
            # if we already have some previous validated entries, starting date is last entry + method period
            if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                last_depreciation_date = fields.Date.from_string(posted_depreciation_line_ids[-1].depreciation_date)
                depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
            else:
                # depreciation_date computed from the purchase date
                depreciation_date = self.date
                #purchase_date = self._get_purchase_date()
                if self.date_first_depreciation == 'last_curr_period':
                    # depreciation_date = the last day of the month
                    depreciation_date = depreciation_date + relativedelta(day=31)
                    # ... or fiscalyear depending the number of period
                    if self.method_period == 12:
                        depreciation_date = depreciation_date + relativedelta(month=int(self.company_id.fiscalyear_last_month))
                        depreciation_date = depreciation_date + relativedelta(day=int(self.company_id.fiscalyear_last_day))
                        if depreciation_date < self.date:
                            depreciation_date = depreciation_date + relativedelta(years=1)
                elif self.date_first_depreciation == 'last_next_period':
                    # depreciation_date = the last day of the month
                    depreciation_date = depreciation_date + relativedelta(months=1,day=31)
                    # ... or fiscalyear depending the number of period
                    if self.method_period == 12:
                        depreciation_date = depreciation_date + relativedelta(month=int(self.company_id.fiscalyear_last_month))
                        depreciation_date = depreciation_date + relativedelta(day=int(self.company_id.fiscalyear_last_day))
                        if depreciation_date < self.date:
                            depreciation_date = depreciation_date + relativedelta(years=1)
                elif self.first_depreciation_manual_date and self.first_depreciation_manual_date != self.date:
                    # depreciation_date set manually from the 'first_depreciation_manual_date' field
                    depreciation_date = self.first_depreciation_manual_date
            first_depreciation_date = depreciation_date# + relativedelta(months=-self.method_period)
            total_days = (depreciation_date.year % 4) and 365 or 366
            month_day = depreciation_date.day
            undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)
            prorata = self.prorata and not self.env.context.get("ignore_prorata")
            #for asset_sequence in range(starting_sequence + 1, depreciation_number + 1):
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                sequence = x + 1
                move_ref = (self.code or '') + self.name + ' (%s/%s)' % (sequence, self.method_number)
                amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr,
                                                    undone_dotation_number, posted_depreciation_line_ids,
                                                    total_days, depreciation_date)
                amount = self.currency_id.round(amount)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount
                if purchase_date and self.date.month >= purchase_date.month:
                    purchase_date = purchase_date + relativedelta(months=+self.method_period)
                    depreciation_date = first_depreciation_date
                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': move_ref,#(self.code or '') + '/' + str(sequence),
                    'remaining_value': residual_amount,
                    'depreciated_value': self.value - (self.salvage_value + residual_amount),
                    'depreciation_date': depreciation_date,
                }
                commands.append((0, False, vals))

                depreciation_date = depreciation_date + relativedelta(months=+self.method_period)

                if month_day > 28 and self.date_first_depreciation == 'manual':
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=min(max_day_in_month, month_day))

                # datetime doesn't take into account that the number of days is not the same for each month
                if not self.prorata and self.method_period % 12 != 0 and self.date_first_depreciation != 'manual':
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)

        self.write({'depreciation_line_ids': commands})

        return True

    def validate(self):
        #self.write({'state': 'open'})
        fields = [
            'method',
            'method_number',
            'method_period',
            'method_end',
            'method_progress_factor',
            'method_time',
            'salvage_value',
            'invoice_id',
        ]
        ref_tracked_fields = self.env['account.asset.asset'].fields_get(fields)
        for asset in self.filtered(lambda a: a.state == 'draft'):
            tracked_fields = ref_tracked_fields.copy()
            if asset.method == 'linear':
                del(tracked_fields['method_progress_factor'])
            if asset.method_time != 'end':
                del(tracked_fields['method_end'])
            else:
                del(tracked_fields['method_number'])
            dummy, tracking_value_ids = asset._mail_track(tracked_fields, dict.fromkeys(fields))
            asset.message_post(subject=_('Asset created'), tracking_value_ids=tracking_value_ids)
            asset.write({'state': 'open'})

    def set_to_close(self):
        move_ids = self._get_disposal_moves()
        if move_ids:
            return self._return_disposal_view(move_ids)
        # Fallback, as if we just clicked on the smartbutton
        # self.write({'state': 'close'})
        for asset in self:
            if asset.state != 'to be dispose':
                raise UserError(_("You cannot close for status %s on asset %s" % (asset.state.title(), asset.name)))
            asset.write({'state': 'close'})
        return self.open_entries()

    def set_to_draft(self):
        self.write({'state': 'draft'})
        
    def _return_disposal_view(self, move_ids):
        name = _('Disposal Move')
        view_mode = 'form'
        if len(move_ids) > 1:
            name = _('Disposal Moves')
            view_mode = 'tree,form'
        return {
            'name': name,
            'view_type': 'form',
            'view_mode': view_mode,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': move_ids[0],
        }

    def _get_disposal_moves(self):
        move_ids = []
        for asset in self:
            total_depreciation_line_ids = sum(asset.depreciation_line_ids.filtered(lambda x: x.move_check).mapped('amount'))
            unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check)
            #print ('=====',total_depreciation_line_ids,unposted_depreciation_line_ids)
            if unposted_depreciation_line_ids:
                #IF DEPRECIATED ALREADY POSTED NOT ALL
                old_values = {
                    'method_end': asset.method_end,
                    'method_number': asset.method_number,
                }
                # Remove all unposted depr. lines
                commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

                # Create a new depr. line with the residual amount and post it
                sequence = len(asset.depreciation_line_ids) - len(unposted_depreciation_line_ids) + 1
                today = fields.Datetime.today()
                vals = {
                    'amount': -total_depreciation_line_ids,#asset.value_residual, #total already deprecated value
                    'asset_id': asset.id,
                    'sequence': sequence,
                    'name': (asset.code or '') + asset.name + ' (%s/%s)' % (str(sequence), 'Closed'),
                    'remaining_value': 0,
                    'depreciated_value': asset.value - asset.salvage_value,  # the asset is completely depreciated
                    'depreciation_date': today,
                }
                commands.append((0, False, vals))
                asset.write({'depreciation_line_ids': commands, 'method_end': today, 'method_number': sequence})
                tracked_fields = self.env['account.asset.asset'].fields_get(['method_number', 'method_end'])
                changes, tracking_value_ids = asset._mail_track(tracked_fields, old_values)
                if changes:
                    asset.message_post(subject=_('Asset sold or disposed. Accounting entry awaiting for validation.'), tracking_value_ids=tracking_value_ids)
                move_ids += asset.depreciation_line_ids[-1].create_move(post_move=False)
            elif total_depreciation_line_ids:
                #IF DEPRECIATED ALREADY POSTED ALL
                old_values = ({
                    'method_end': asset.method_end,
                    'method_number': asset.method_number,
                })
                #'line_ids': [(0, 0, line) for line in move_lines]
                # Remove all unposted depr. lines
                commands = []
                # Create a new depr. line with the residual amount and post it
                sequence = 1#len(asset.depreciation_line_ids) - len(unposted_depreciation_line_ids) + 1
                today = fields.Datetime.today()
                vals = {
                    'amount': -total_depreciation_line_ids,#asset.value_residual, #total already deprecated value
                    'asset_id': asset.id,
                    'sequence': sequence,
                    'name': (asset.code or '') + asset.name + ' (%s/%s)' % (str(sequence), 'Closed'),
                    'remaining_value': 0,
                    'depreciated_value': (asset.value - asset.salvage_value) if not self.env.context.get('recreate_asset') else 0,# the asset is completely depreciated
                    'depreciation_date': today,
                    #'method_end': asset.method_end,
                    #'method_number': asset.method_number,
                }
                #[(0, 0, line) for line in move_lines]
                commands.append((0, False, vals))
                asset.write({'depreciation_line_ids': commands})
                tracked_fields = self.env['account.asset.asset'].fields_get(['method_number', 'method_end'])
                changes, tracking_value_ids = asset._mail_track(tracked_fields, old_values)
                if changes:
                    asset.message_post(subject=_('Asset sold or disposed. Accounting entry awaiting for validation.'), tracking_value_ids=tracking_value_ids)
                move_ids += asset.depreciation_line_ids[-1].create_move(post_move=False)
        #print ('=move_ids==',move_ids)
        return move_ids

    @api.depends('value', 'salvage_value', 'depreciation_line_ids.move_check', 'depreciation_line_ids.amount')
    def _amount_residual(self):
        for rec in self:
            total_amount = 0.0
            for line in rec.depreciation_line_ids:
                if line.move_check:
                    total_amount += line.amount
            rec.value_residual = rec.value - total_amount - rec.salvage_value
            # rec.value_monthly = rec.value_residual / (rec.method_number or 1.0)
            # rec.depreciation_number = rec.value_residual / (rec.method_number or 1.0)
            # rec.depreciation_amount = rec.value_residual / (rec.method_number or 1.0)

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.currency_id = self.company_id.currency_id.id

    @api.onchange('date_first_depreciation')
    def onchange_date_first_depreciation(self):
        for record in self:
            if record.date_first_depreciation == 'manual':
                record.first_depreciation_manual_date = record.date

    # @api.depends('depreciation_line_ids.move_id')
    # def _entry_count(self):
    #     for asset in self:
    #         res = self.env['account.asset.depreciation.line'].search_count([('asset_id', '=', asset.id), ('move_id', '!=', False)])
    #         asset.entry_count = res or 0

    @api.constrains('prorata', 'method_time')
    def _check_prorata(self):
        if self.prorata and self.method_time != 'number':
            raise ValidationError(_('Prorata temporis can be applied only for the "number of depreciations" time method.'))

    @api.onchange('category_id')
    def onchange_category_id(self):
        vals = self.onchange_category_id_values(self.category_id.id)
        #print ('==onchange_category_id_values==',vals)
        # We cannot use 'write' on an object that doesn't exist yet
        if vals:
            for k, v in vals['value'].items():
                setattr(self, k, v)

    def onchange_category_id_values(self, category_id):
        if category_id:
            category = self.env['account.asset.category'].browse(category_id)
            #print ('===category===',category)
            return {
                'value': {
                    'method': category.method,
                    #'method_number': category.method_number,
                    'method_time': category.method_time,
                    'method_period': category.method_period,
                    'method_progress_factor': category.method_progress_factor,
                    'method_end': category.method_end,
                    'prorata': category.prorata,
                    'date_first_depreciation': category.date_first_depreciation,
                    'account_analytic_id': category.account_analytic_id.id,
                    'analytic_tag_ids': [(6, 0, category.analytic_tag_ids.ids)],
                }
            }

    @api.onchange('method_time')
    def onchange_method_time(self):
        if self.method_time != 'number':
            self.prorata = False

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['name'] = self.name + _(' (copy)')
        return super(AccountAssetAsset, self).copy_data(default)

    def _compute_entries(self, date, group_entries=False):
        depreciation_ids = self.env['account.asset.depreciation.line'].search([
            ('asset_id', 'in', self.ids), ('depreciation_date', '<=', date),
            ('move_check', '=', False)])
        if group_entries:
            return depreciation_ids.create_grouped_move()
        return depreciation_ids.create_move()

    @api.model
    def create(self, vals):
        asset = super(AccountAssetAsset, self.with_context(mail_create_nolog=True)).create(vals)
        asset.sudo().compute_depreciation_board()
        return asset

    def write(self, vals):
        res = super(AccountAssetAsset, self).write(vals)
        if 'depreciation_line_ids' not in vals and 'state' not in vals:
            for rec in self:
                rec.compute_depreciation_board()
        return res

    # def open_entries(self):
    #     move_ids = []
    #     for asset in self:
    #         for depreciation_line in asset.depreciation_line_ids:
    #             if depreciation_line.move_id:
    #                 move_ids.append(depreciation_line.move_id.id)
    #     return {
    #         'name': _('Journal Entries'),
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', move_ids)],
    #     }

    def open_depre_lines(self):
        return {
            'name': _('Depreciation Boards'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.depreciation.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('asset_id', '=', self.id)],
        }

    def open_entries(self):
        move_ids = []
        for asset in self:
            for depreciation_line in asset.depreciation_line_ids:
                if depreciation_line.move_id:
                    move_ids.append(depreciation_line.move_id.id)

        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['name'] = _('Journal Entries')
        action['domain'] = [('id', 'in', move_ids)]
        action['context'] = {
            #'default_location_id': self.location_id.id,
            #'default_product_id': self.product_id.id,
            #'default_lot_id': self.lot_id.id,
            # 'search_default_coa': 1,
            # 'search_default_done': 1,
            # 'create': 0,
            # 'default_picking_id': self.id,
        }
        return action

class AccountAssetDepreciationLine(models.Model):
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    name = fields.Char(string='Depreciation Name', required=True, index=True)
    sequence = fields.Integer(required=True)
    asset_id = fields.Many2one('account.asset.asset', string='Asset', required=True, ondelete='cascade')
    parent_state = fields.Selection(related='asset_id.state', string='State of Asset')
    amount = fields.Float(string='Current Depreciation', digits=0, required=True)
    remaining_value = fields.Float(string='Next Period Depreciation', digits=0, required=True)
    depreciated_value = fields.Float(string='Cumulative Depreciation', required=True)
    depreciation_date = fields.Date('Depreciation Date', index=True)
    move_id = fields.Many2one('account.move', string='Depreciation Entry')
    move_check = fields.Boolean(compute='_get_move_check', string='Linked', store=True)
    move_posted_check = fields.Boolean(compute='_get_move_posted_check', string='Posted', store=True)
    closed = fields.Boolean('Closed', default=False)

    @api.depends('move_id')
    def _get_move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    @api.depends('move_id.state')
    def _get_move_posted_check(self):
        for line in self:
            line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        for line in self:
            if line.move_id:
                raise UserError(_('This depreciation is already linked to a journal entry. Please post or delete it.'))
            move_vals = self._prepare_move(line)
            move = self.env['account.move'].create(move_vals)
            line.write({'move_id': move.id, 'move_check': True})
            created_moves |= move

        if post_move and created_moves:
            created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).action_post()
        return [x.id for x in created_moves]

    def _prepare_move(self, line):
        category_id = line.asset_id.category_id
        account_analytic_id = line.asset_id.account_analytic_id
        analytic_tag_ids = line.asset_id.analytic_tag_ids
        depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
        company = line.asset_id.company_id
        company_currency = company.currency_id
        current_currency = line.asset_id.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(line.amount, company_currency, line.asset_id.company_id, depreciation_date)
        asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
        account_expense_id = line.asset_id.account_depreciation_expense_id.id or category_id.account_depreciation_expense_id.id
        move_lines = []
        #move_line_1 =
        #print ('#AKUM DIDEBITKAN',amount)
        move_lines.append({
            'name': asset_name,
            'account_id': category_id.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'partner_id': line.asset_id.partner_id.id,
            'analytic_account_id': account_analytic_id.id if category_id.asset_type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.asset_type == 'sale' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
            #'is_depreciation': True,
        })
        depreciated_value = current_currency._convert(line.depreciated_value, company_currency, line.asset_id.company_id, depreciation_date)
        if amount < 0 and depreciated_value:
            #print ('#NILAI ASET DIKREDITKAN',depreciated_value)
            move_lines.append({
                'name': asset_name,
                'account_id': category_id.account_asset_id.id,
                'debit': 0.0 if float_compare(depreciated_value, 0.0, precision_digits=prec) > 0 else -depreciated_value,
                'credit': depreciated_value if float_compare(depreciated_value, 0.0, precision_digits=prec) > 0 else 0.0,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': account_analytic_id.id if category_id.asset_type == 'sale' else False,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.asset_type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
                #'is_depreciation': True,
            })
            amount = depreciated_value + amount
            #GANTI AKUN/SAMA KALAU ASET HABIS
            account_expense_id = category_id.account_depreciation_disposal_id.id or account_expense_id
            #print ('====',depreciated_value,amount)
        if amount:
            #print ('#EXP AKUN DIDEBITKAN',amount)
            move_lines.append({
                'name': asset_name,
                'account_id': account_expense_id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': account_analytic_id.id if category_id.asset_type == 'purchase' else False,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.asset_type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and line.amount or 0.0,
                #'is_depreciation': True,
            })
        #print ('===move_lines==',move_lines)
        move_vals = {
            'is_depreciation': True,
            'ref': line.asset_id.code,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': [(0, 0, line) for line in move_lines],#move_lines,#[(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        return move_vals

    def _prepare_move_grouped(self):
        asset_id = self[0].asset_id
        category_id = asset_id.category_id  # we can suppose that all lines have the same category
        account_analytic_id = asset_id.account_analytic_id
        analytic_tag_ids = asset_id.analytic_tag_ids
        depreciation_date = self.env.context.get('depreciation_date') or fields.Date.context_today(self)
        prec = company_currency.decimal_places
        amount = 0.0
        #asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
        account_expense_id = line.asset_id.account_depreciation_expense_id.id or category_id.account_depreciation_expense_id.id
        for line in self:
            # Sum amount of all depreciation lines
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            company = line.asset_id.company_id
            amount += current_currency._convert(line.amount, company_currency, company, fields.Date.today())

        move_lines = []
        name = category_id.name + _(' (grouped)')
        move_lines.append({
            'name': name,
            'account_id': category_id.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'journal_id': category_id.journal_id.id,
            'analytic_account_id': account_analytic_id.id if category_id.asset_type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.asset_type == 'sale' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * amount or 0.0,
        })
        if amount < 0:
            #NILAI ASET DIKREDITKAN
            depreciated_value = current_currency._convert(line.depreciated_value, company_currency, line.asset_id.company_id, depreciation_date)
            move_lines.append({
                'name': name,
                'account_id': category_id.account_asset_id.id,
                'debit': 0.0 if float_compare(depreciated_value, 0.0, precision_digits=prec) > 0 else -depreciated_value,
                'credit': depreciated_value if float_compare(depreciated_value, 0.0, precision_digits=prec) > 0 else 0.0,
                'partner_id': line.asset_id.partner_id.id,
                'analytic_account_id': account_analytic_id.id if category_id.asset_type == 'sale' else False,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.asset_type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * amount or 0.0,
            })
            amount = depreciated_value + amount
            #GANTI AKUN/SAMA KALAU ASET HABIS
            account_expense_id = category_id.account_depreciation_disposal_id.id or account_expense_id
        if amount:
            move_lines.append({
                'name': name,
                'account_id': account_expense_id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': category_id.journal_id.id,
                'analytic_account_id': account_analytic_id.id if category_id.asset_type == 'purchase' else False,
                'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.asset_type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * amount or 0.0,
            })
        move_vals = {
            'ref': category_id.name,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': [(0, 0, line) for line in move_lines],
        }
        #move_ref = self.name + ' (%s/%s)' % (prorata and asset_sequence - 1 or asset_sequence, self.method_number)
        return move_vals

    def create_grouped_move(self, post_move=True):
        if not self.exists():
            return []

        created_moves = self.env['account.move']
        move = self.env['account.move'].create(self._prepare_move_grouped())
        self.write({'move_id': move.id, 'move_check': True})
        created_moves |= move

        if post_move and created_moves:
            created_moves.action_post()
        return [x.id for x in created_moves]

    def post_lines_and_close_asset(self):
        # we re-evaluate the assets to determine whether we can close them
        for line in self:
            line.log_message_when_posted()
            asset = line.asset_id
            if asset.currency_id.is_zero(asset.value_residual):
                asset.message_post(body=_("Document closed."))
                asset.write({'state': 'close'})

    def log_message_when_posted(self):
        def _format_message(message_description, tracked_values):
            message = ''
            if message_description:
                message = '<span>%s</span>' % message_description
            for name, values in tracked_values.items():
                message += '<div> &nbsp; &nbsp; &bull; <b>%s</b>: ' % name
                message += '%s</div>' % values
            return message

        for line in self:
            if line.move_id and line.move_id.state == 'draft':
                partner_name = line.asset_id.partner_id.name
                currency_name = line.asset_id.currency_id.name
                msg_values = {_('Currency'): currency_name, _('Amount'): line.amount}
                if partner_name:
                    msg_values[_('Partner')] = partner_name
                msg = _format_message(_('Depreciation line posted.'), msg_values)
                line.asset_id.message_post(body=msg)
    
    def unlink(self):
        for record in self:
            if record.move_check:
                if record.asset_id.category_id.asset_type == 'purchase':
                    msg = _("You cannot delete posted depreciation lines.")
                else:
                    msg = _("You cannot delete posted installment lines.")
                raise UserError(msg)
        return super(AccountAssetDepreciationLine, self).unlink()
