# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('line_ids.account_id.asset_category_id')
    def _get_asset_lines(self):
        for move in self:
            move.has_asset_line = any(move.line_ids.mapped('asset_category_id'))#any(move.line_ids.mapped('account_id').mapped('asset_category_id'))

    method_number = fields.Integer(string='Number of Depreciations', default=0, help="The number of depreciations needed to depreciate your asset")
    is_depreciation = fields.Boolean('Is Depreciation', default=False)
    has_asset_line = fields.Boolean(compute='_get_asset_lines')
    asset_id = fields.Many2one('account.asset.asset', string='Asset', index=True, ondelete='cascade', copy=False, domain="[('company_id', '=', company_id)]")
    asset_depreciation_ids = fields.One2many('account.asset.depreciation.line', 'move_id', string='Assets Depreciation Lines')
    asset_type = fields.Selection(related='asset_id.asset_type')
    # asset_remaining_value = fields.Monetary(string='Depreciable Value', copy=False)
    # asset_depreciated_value = fields.Monetary(string='Cumulative Depreciation', copy=False)
    # asset_manually_modified = fields.Boolean(help='This is a technical field stating that a depreciation line has been manually modified. It is used to recompute the depreciation table of an asset/deferred revenue.', copy=False)
    # asset_value_change = fields.Boolean(help='This is a technical field set to true when this move is the result of the changing of value of an asset')
    asset_ids = fields.One2many('account.asset.asset', string='Assets', compute="_compute_asset_ids")
    # asset_ids_display_name = fields.Char(compute="_compute_asset_ids")  # just a button label. That's to avoid a plethora of different buttons defined in xml
    asset_display_name = fields.Char(compute="_compute_asset_ids")   # just a button label. That's to avoid a plethora of different buttons defined in xml
    number_asset_ids = fields.Integer(compute="_compute_asset_ids")
    # draft_asset_ids = fields.Boolean(compute="_compute_asset_ids")


    @api.depends('line_ids.asset_ids')
    def _compute_asset_ids(self):
        for record in self:
            record.asset_ids = record.mapped('line_ids.asset_ids')
            record.number_asset_ids = len(record.asset_ids)
            if record.number_asset_ids:
                asset_type = {
                    'sale': _('Deferred Revenue(s)'),
                    'purchase': _('Asset(s)'),
                    'expense': _('Deferred Expense(s)')
                }
                record.asset_display_name = '%s %s' % (len(record.asset_ids), asset_type.get(record.asset_ids[0].asset_type))
            else:
                record.asset_display_name = ''
            record.asset_display_name = {'sale': _('Revenue'), 'purchase': _('Asset'), 'expense': _('Expense')}.get(record.asset_id.asset_type)
            #record.draft_asset_ids = bool(record.asset_ids.filtered(lambda x: x.state == "draft"))

    # def _post(self, soft=True):
    #     # OVERRIDE
    #     posted = super()._post(soft)

    #     # log the post of a depreciation
    #     #posted._log_depreciation_asset()

    #     # look for any asset to create, in case we just posted a bill on an account
    #     # configured to automatically create assets
    #     posted._auto_create_asset()
    #     # check if we are reversing a move and delete assets of original move if it's the case
    #     #posted._delete_reversed_entry_assets()

    #     # close deferred expense/revenue if all their depreciation moves are posted
    #     #posted._close_assets()

    #     return posted

    # @api.model
    # def _refund_cleanup_lines(self, lines):
    #     result = super(AccountMove, self)._refund_cleanup_lines(lines)
    #     for i, line in enumerate(lines):
    #         for name, field in line._fields.items():
    #             if name == 'asset_category_id':
    #                 result[i][2][name] = False
    #                 break
    #     return result

    # def button_cancel(self):
    #     for move in self:
    #         for line in move.asset_depreciation_ids:
    #             line.move_posted_check = False
    #     return super(AccountMove, self).button_cancel()

    # def action_cancel(self):
    #     res = super(AccountMove, self).action_cancel()
    #     self.env['account.asset.asset'].sudo().search([('invoice_id', 'in', self.ids)]).write({'active': False})
    #     return res

    def action_post(self):
        result = super(AccountMove, self).action_post()
        for inv in self:
            context = dict(self.env.context)
            context.pop('default_type', None)
            if not self.env.context.get('method_number'):
                print ('#GENERATE ASSET/PREPAID JIKA ADA CATEGORY DAN METHOD NUMBER != 0 DAN JIKA DISALAH SATU LINE BOLEH CREATE ASSET',any(inv.line_ids.filtered(lambda line: line.account_id.create_asset != 'no' and line.account_id.asset_type != 'purchase')))
                if not inv.method_number and any(inv.line_ids.filtered(lambda line: line.asset_category_id and line.account_id.create_asset != 'no' and line.account_id.asset_type != 'purchase')):
                    raise UserError(_('The number of depreciations or the period length of your asset cannot be 0.'))
                context.update(method_number=inv.method_number)
            # print ('===action_post===',context)
            for mv_line in inv.line_ids.filtered(lambda line: line.account_id.create_asset != 'no'):
                #context.update(method_number=mv_line.quantity)
                mv_line.with_context(context).asset_create()
        return result

    def open_asset_view(self):
        ret = {
            'name': _('Assets'),
            'view_mode': 'form',
            'res_model': 'account.asset.asset',
            'view_id': [v[0] for v in self.env['account.asset.asset']._get_views(self.asset_type) if v[1] == 'form'][0],
            'type': 'ir.actions.act_window',
            'res_id': self.asset_id.id,
            'context': dict(self._context, create=False),
        }
        if self.asset_ids[0].asset_type == 'sale':
            ret['name'] = _('Deferred Revenue')
        elif self.asset_ids[0].asset_type == 'expense':
            ret['name'] = _('Prepaid Expense')
        return ret

    def action_open_asset_ids(self):
        ret = {
            'name': _('Assets'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.asset',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.asset_ids.ids)],
            'views': self.env['account.asset.asset']._get_views(self.asset_ids[0].asset_type),
        }
        if self.asset_ids[0].asset_type == 'sale':
            ret['name'] = _('Deferred Revenues')
        elif self.asset_ids[0].asset_type == 'expense':
            ret['name'] = _('Prepaid Expenses')
        return ret

    
    # def action_post(self):
    #     for move in self:
    #         for depreciation_line in move.asset_depreciation_ids:
    #             depreciation_line.post_lines_and_close_asset()
    #     return super(AccountMove, self).action_post()
        

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_category_id = fields.Many2one('account.asset.category', string='Asset Category')
    asset_start_date = fields.Date(string='Asset Start Date', compute='_get_asset_date', readonly=True, store=True)
    asset_end_date = fields.Date(string='Asset End Date', compute='_get_asset_date', readonly=True, store=True)
    asset_mrr = fields.Float(string='Monthly Recurring Revenue', compute='_get_asset_date', readonly=True, digits="Account", store=True)
    create_asset = fields.Selection([('no', 'No'), ('draft', 'Create in draft'),('validate', 'Create and validate')], related='account_id.create_asset', required=False, store=True)
    asset_ids = fields.Many2many('account.asset.asset', 'asset_asset_move_line_rel', 'line_id', 'asset_id', string='Asset Linked', help="Asset created from this Journal Item", copy=False)
    #is_depreciation = fields.Boolean('Is Depreciation', default=False)

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveLine, self).default_get(fields)
        if self.env.context.get('create_bill'):
            if self.product_id and self.move_id.move_type == 'out_invoice' and \
                    self.product_id.product_tmpl_id.deferred_revenue_category_id:
                self.asset_category_id = self.product_id.product_tmpl_id.deferred_revenue_category_id.id
            elif self.product_id and self.product_id.product_tmpl_id.asset_category_id and \
                    self.move_id.move_type == 'in_invoice':
                self.asset_category_id = self.product_id.product_tmpl_id.asset_category_id.id
            # self.onchange_asset_category_id()
        return res

    @api.depends('asset_category_id', 'move_id.invoice_date')
    def _get_asset_date(self):
        for rec in self.filtered(lambda ml: ml.asset_category_id):
            rec.asset_mrr = 0
            rec.asset_start_date = False
            rec.asset_end_date = False
            cat = rec.asset_category_id
            if cat:
                if (rec.move_id.method_number == 0 or cat.method_period == 0) and rec.asset_category_id.asset_type != 'purchase':
                    raise UserError(_('The number of depreciations or the period length of your asset category cannot be 0.'))
                months = rec.move_id.method_number * cat.method_period
                if rec.move_id.move_type in ['out_invoice', 'out_refund']:
                    rec.asset_mrr = rec.price_subtotal / months
                if rec.move_id.invoice_date:
                    start_date = rec.move_id.invoice_date.replace(day=1)
                    end_date = (start_date + relativedelta(months=months, days=-1))
                    rec.asset_start_date = start_date
                    rec.asset_end_date = end_date

    def _prepare_asset_data(self):
        #AMBIL ASET CATEGORY DARI JOURNAL ITEM JIKA TIDAK ADA AMBIL DR SETTINGAN ACCOUNT
        asset_category_id = (self.asset_category_id.id or self.account_id.asset_category_id.id) if self.account_id.create_asset in ('draft','validate') else False
        asset_type = (self.asset_category_id.asset_type or self.account_id.asset_category_id.asset_type) if self.account_id.create_asset in ('draft','validate') else ''
        #AMBIL JUMLAH DEPRESIASI DARI CONTEXT method_number JIKA TIDAK AMBIL DR SETTINGAN CATEGORY JIKA TIDAK AMBIL DARI SETTINGAN ACCOUNT
        method_number = self.move_id.method_number or self.asset_category_id.method_number or self.account_id.asset_category_id.method_number
        vals = {
            'name': self.name,
            'code': '/' or False,
            'method_number': method_number,
            'category_id': asset_category_id,
            'asset_type': asset_type,
            'value': abs(self.debit - self.credit) / (self.quantity or 1.0),
            'partner_id': self.move_id.partner_id.id,
            'company_id': self.move_id.company_id.id,
            'currency_id': self.move_id.company_currency_id.id,
            'date': self.move_id.date,
            'invoice_id': self.move_id.id,
            'original_move_line_ids': [(6, False, self.ids)],
        }
        #print ('==om_account_asset==_prepare_asset_data==',vals)
        return vals
        
    def asset_create(self):
        #print ('#CREATE ASSET / PREPAID JIKA BELUM ADA DAN ADA CATEGORY DAN JIKA AKUN BOLEH CREATE ASSET',self.account_id.create_asset,self.asset_ids)
        if self.account_id.create_asset in ('draft','validate') and self.asset_category_id and not self.asset_ids:
            #quantity = self.quantity if self.env.context.get('multi_asset_per_qty') else 1
            multi_asset_per_qty = self.env.context.get('multi_asset_per_qty')
            stock_line_ids = self.env.context.get('stock_line_ids') or []
            #print ('===stock_line_ids===',stock_line_ids)
            if stock_line_ids:
                for stock_line_id in stock_line_ids:
                    vals = self.with_context(method_number=self.env.context.get('method_number'), multi_asset_per_qty=multi_asset_per_qty, stock_line_id=stock_line_id)._prepare_asset_data()
                    changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
                    vals.update(changed_vals['value'])
                    asset = self.env['account.asset.asset'].create(vals)
                    asset._onchange_date()
                    if self.account_id.asset_category_id.open_asset:
                        asset.validate()
            else:
                vals = self.with_context(method_number=self.env.context.get('method_number'))._prepare_asset_data()
                changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
                vals.update(changed_vals['value'])
                asset = self.env['account.asset.asset'].create(vals)
                asset._onchange_date()
                if self.account_id.asset_category_id.open_asset:
                    asset.validate()
        return True

    # @api.onchange('asset_category_id')
    # def onchange_asset_category_id(self):
    #     if self.move_id.move_type == 'out_invoice' and self.asset_category_id:
    #         self.account_id = self.asset_category_id.account_asset_id.id
    #     elif self.move_id.move_type == 'in_invoice' and self.asset_category_id:
    #         self.account_id = self.asset_category_id.account_asset_id.id

    # @api.onchange('product_uom_id')
    # def _onchange_uom_id(self):
    #     result = super(AccountMoveLine, self)._onchange_uom_id()
    #     self.onchange_asset_category_id()
    #     return result

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     vals = super(AccountMoveLine, self)._onchange_product_id()
    #     for rec in self:
    #         if rec.product_id:
    #             if rec.move_id.move_type == 'out_invoice':
    #                 rec.asset_category_id = rec.product_id.product_tmpl_id.deferred_revenue_category_id.id
    #             elif rec.move_id.move_type == 'in_invoice':
    #                 rec.asset_category_id = rec.product_id.product_tmpl_id.asset_category_id.id
    #     return vals

    # def get_invoice_line_account(self, type, product, fpos, company):
    #     return product.asset_category_id.account_asset_id or super(AccountMoveLine, self).get_invoice_line_account(type, product, fpos, company)


    def _turn_as_asset(self, asset_type, view_name, view):
        ctx = self.env.context.copy()
        if self.account_id.create_asset == 'no':
            raise UserError(_("This Account journal item should be from the allowed Create Asset %s", self.name))
        #print ('==asset_type==',asset_type)
        ctx.update({
            'default_original_move_line_ids': [(6, False, self.env.context['active_ids'])],
            'default_company_id': self.company_id.id,
            'asset_type': asset_type,
            'default_category_id': self.account_id.asset_category_id.id,
            'default_name': self.name,
        })
        if any(line.move_id.state == 'draft' for line in self):
            raise UserError(_("All the lines should be posted"))
        if any(account != self[0].account_id for account in self.mapped('account_id')):
            raise UserError(_("All the lines should be from the same account"))
        return {
            "name": view_name,
            "type": "ir.actions.act_window",
            "res_model": "account.asset.asset",
            "views": [[view.id, "form"]],
            "target": "current",
            "context": ctx,
        }

    def turn_as_asset(self):
        if len(self) > 1:
            raise UserError(_("Only can create one asset per item"))
        return self._turn_as_asset('purchase', _("Turn as an asset"), self.env.ref("om_account_asset.view_account_asset_asset_form"))

    def turn_as_deferred(self):
        balance = sum(aml.debit - aml.credit for aml in self)
        if balance > 0:
            return self._turn_as_asset('expense', _("Turn as a deferred expense"), self.env.ref('om_account_asset.view_account_asset_asset_expense_form'))
        else:
            return self._turn_as_asset('sale', _("Turn as a deferred revenue"), self.env.ref('om_account_asset.view_account_asset_asset_revenue_form'))