# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
#from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from num2words import num2words
from odoo.tools import float_is_zero
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

class AccountVoucherType(models.Model):
    _name = 'account.voucher.type'
    _description = 'Account Voucher Type'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    sequence_id = fields.Many2one('ir.sequence',string="Entry Sequence")

class AccountVoucher(models.Model):
    _name = 'account.voucher'
    _description = 'Accounting Voucher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc, id desc"

    @api.model
    def _default_journal(self):
        voucher_type = self._context.get('voucher_type', 'sale')
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', '=', voucher_type),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    
    @api.model
    def _default_payment_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            #('type', 'in', ('bank', 'cash')),
            ('is_voucher','=',True),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    
    def _compute_voucher_docs_count(self):
        Attachment = self.env['ir.attachment']
        for voucher in self:
            voucher.doc_count = Attachment.search_count([
                ('res_model', '=', 'account.voucher'), ('res_id', '=', voucher.id)
            ])
    
    @api.depends('amount_voucher', 'line_ids.price_subtotal')
    def _compute_balance(self):
        for voucher in self:
            voucher.balance = voucher.amount_voucher - voucher.amount

    # @api.depends('move_id.line_ids.full_reconcile_id')
    # def _compute_reconciled(self):
    #     for voucher in self:
    #         voucher.is_reconciled = voucher.move_id.line_ids.filtered(lambda l: l.account_id == ).full_reconcile_id
    #         if voucher.is_reconciled:
    #             voucher.state = 'posted'

    @api.depends('date', 'payment_journal_id')
    def _get_previous_statement(self):
        for st in self:
            # Search for the previous statement
            domain = [('date', '<=', st.date), ('journal_id', '=', st.journal_id.id)]
            # The reason why we have to perform this test is because we have two use case here:
            # First one is in case we are creating a new record, in that case that new record does
            # not have any id yet. However if we are updating an existing record, the domain date <= st.date
            # will find the record itself, so we have to add a condition in the search to ignore self.id
            if not isinstance(st.id, models.NewId):
                domain.extend(['|', '&', ('id', '<', st.id), ('date', '=', st.date), '&', ('id', '!=', st.id), ('date', '!=', st.date)])
            previous_voucher = self.search(domain, limit=1, order='date desc, id desc')
            st.previous_voucher_id = previous_voucher.id

    def _compute_starting_balance(self):
        # When a bank statement is inserted out-of-order several fields needs to be recomputed.
        # As the records to recompute are ordered by id, it may occur that the first record
        # to recompute start a recursive recomputation of field balance_end_real
        # To avoid this we sort the records by date
        for voucher in self.sorted(key=lambda s: s.date):
            if voucher.previous_voucher_id.balance_end_real != voucher.balance_start:
                voucher.balance_start = voucher.previous_voucher_id.balance_end_real
            else:
                # Need default value
                voucher.balance_start = voucher.balance_start or 0.0

    @api.depends('previous_voucher_id', 'previous_voucher_id.balance_end_real')
    def _compute_ending_balance(self):
        latest_voucher = self.env['account.voucher'].search([('payment_journal_id', '=', self[0].payment_journal_id.id)], limit=1)
        for voucher in self:
            # recompute balance_end_real in case we are in a bank journal and if we change the
            # balance_end_real of previous statement as we don't want
            # holes in case we add a statement in between 2 others statements.
            # We only do this for the bank journal as we use the balance_end_real in cash
            # journal for verification and creating cash difference entries so we don't want
            # to recompute the value in that case
            if voucher.payment_journal_id.type == 'bank':
                # If we are on last statement and that statement already has a balance_end_real, don't change the balance_end_real
                # Otherwise, recompute balance_end_real to prevent holes between statement.
                if latest_voucher.id and voucher.id == latest_voucher.id and not float_is_zero(voucher.balance_end_real, precision_digits=voucher.currency_id.decimal_places):
                    voucher.balance_end_real = voucher.balance_end_real or 0.0
                else:
                    total_entry_encoding = sum([line.price_subtotal for line in voucher.line_ids])
                    voucher.balance_end_real = voucher.previous_voucher_id.balance_end_real + total_entry_encoding
            else:
                # Need default value
                voucher.balance_end_real = voucher.balance_end_real or 0.0
                
    @api.depends('line_ids.tax_ids')
    def _compute_has_taxes(self):
        for voucher in self:
            voucher.has_taxes = any(line.tax_ids for line in voucher.line_ids)

    has_taxes = fields.Boolean('Has Taxes', compute='_compute_has_taxes', store=True)   
    doc_count = fields.Integer(compute='_compute_voucher_docs_count', string="Number of documents attached")
    previous_voucher_id = fields.Many2one('account.voucher', help='technical field to compute starting balance correctly', compute='_get_previous_statement', store=True)
    balance_start = fields.Monetary(string='Starting Balance', states={'posted': [('readonly', True)]}, compute='_compute_starting_balance', readonly=False, store=True, tracking=True)
    balance_end_real = fields.Monetary('Ending Balance', states={'posted': [('readonly', True)]}, compute='_compute_ending_balance', recursive=True, readonly=False, store=True, tracking=True)
    priority = fields.Selection(PROCUREMENT_PRIORITIES, string="Priority", default="0")
    voucher_type = fields.Selection([
        ('sale', 'Receipt'),
        ('purchase', 'Payment')
        ], string='Type', readonly=True, states={'draft': [('readonly', False)]}, oldname="type")
    name = fields.Char('Payment Memo',
        #readonly=True, states={'draft': [('readonly', False)]}, 
        default='',copy=False)
    number_invoice = fields.Char('Invoice', readonly=True,
        index=True, states={'draft': [('readonly', False)]})
    number_cheque = fields.Char('Cheque', readonly=True,
        index=True, states={'draft': [('readonly', False)]})
    date = fields.Date("Bill Date", readonly=True,
        index=True, states={'draft': [('readonly', False)]},
        copy=False, default=fields.Date.context_today)
    account_date = fields.Date("Accounting Date",
        readonly=True, index=True, states={'draft': [('readonly', False)]},
        help="Effective date for accounting entries", copy=False, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', 'Journal',
        required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_default_journal,
        domain="[('type', 'in', {'sale': ['sale'], 'purchase': ['purchase']}.get(voucher_type, [])), ('company_id', '=', company_id)]")
    payment_journal_id = fields.Many2one('account.journal', string='Payment Method', readonly=True,
        states={'draft': [('readonly', False)]}, domain="[('is_voucher', '=', True)]", 
        default=_default_payment_journal)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
#     account_id = fields.Many2one('account.account', 'Account',
#         required=True, readonly=True, states={'draft': [('readonly', False)]},
#         domain="[('deprecated', '=', False), ('internal_type','=', (voucher_type == 'purchase' and 'payable' or 'receivable'))]")
    line_ids = fields.One2many('account.voucher.line', 'voucher_id', 'Voucher Lines', copy=True,
        states={'posted': [('readonly', True)]})
    narration = fields.Text('Notes')#, readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', compute='_get_journal_currency',
        string='Currency', readonly=True, store=True, default=lambda self: self._get_currency())
    # currency_id = fields.Many2one('res.currency', string='Currency', required=True, 
    #     readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', 'Company',
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirm'),
        #('waiting_approval','Waiting Approval'),
        #('approved', 'Approved'),
        ('in_payment', 'In Payment'),
        ('posted', 'Posted'),
        ], 'Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Voucher.\n"
             " * The 'Pro-forma' status is used when the voucher does not have a voucher number.\n"
             " * The 'Posted' status is used when user create voucher,a voucher number is generated and voucher entries are created in account.\n"
             " * The 'Cancelled' status is used when user cancel voucher.")
    reference = fields.Char('Bill Reference', readonly=True, states={'draft': [('readonly', False)]},
                                 help="The partner reference of this document.", copy=False)
    amount = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_total')
    tax_amount = fields.Monetary(readonly=True, store=True, compute='_compute_total')
    tax_correction = fields.Monetary(readonly=True, states={'draft': [('readonly', False)]},
        help='In case we have a rounding problem in the tax, use this field to correct it')
    #number = fields.Char(readonly=True, copy=False)
    move_id = fields.Many2one('account.move', 'Journal Entry', copy=False, check_company=True)
    #is_reconciled = fields.Boolean(string='Is Reconciled', compute='_compute_reconciled', store=True)
    # move_id = fields.Many2one(
    #     comodel_name='account.move',
    #     string='Journal Entry', required=False, readonly=True, ondelete='cascade', copy=False,
    #     check_company=True)
    partner_id = fields.Many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft': [('readonly', False)]})
    paid = fields.Boolean(compute='_check_paid', help="The Voucher has been totally paid.")
    pay_now = fields.Selection([
            ('pay_now', 'Pay Directly'),
            ('pay_later', 'Pay Later'),
        ], 'Payment', index=True, readonly=True, states={'draft': [('readonly', False)]}, default='pay_later')
    date_due = fields.Date('Due Date', readonly=True, index=True, states={'draft': [('readonly', False)]})
    
    user_id = fields.Many2one('res.users', string='Responsible', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    number = fields.Char(readonly=False, copy=False, default=lambda self: _('New'))
    account_id = fields.Many2one('account.account', 'Account', required=True, readonly=True, states={'draft': [('readonly', False)]},  domain="[('deprecated', '=', False)]")
    type = fields.Many2one('account.voucher.type', string='Transaction Type', readonly=True,
        index=True, states={'draft': [('readonly', False)]})
    transaction_type = fields.Selection([
            #('expedition', 'Expedition'), 
            ('regular', 'Regular'),
            #('disposal','Asset Disposal')
            ], string='Voucher Type', default='regular', readonly=True, states={'draft': [('readonly', False)]})
    amount_voucher = fields.Monetary(string='Amount',states={'posted':[('readonly',True)]})
    balance = fields.Monetary(string='Balance', store=True, readonly=True, compute='_compute_balance')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=True,
        index=True, states={'draft': [('readonly', False)]})
    summary_description = fields.Text('Summary Description', compute='_summary_voucher_line', store=True)
    #terbilang
    terbilang = fields.Char(string="Terbilang",compute="_compute_terbilang",store=True)

    @api.depends('voucher_type')
    def _compute_type(self):
        return
        # for voucher in self:
        #     if voucher.voucher_type == 'sale':
        #         voucher.type = self.env['account.voucher.type'].search([('name', '=', 'Receipt Voucher')], limit=1) 
        #     elif voucher.voucher_type == 'purchase': 
        #         voucher.type = self.env['account.voucher.type'].search([('name', '=', 'Payment Voucher')], limit=1)

    @api.depends('line_ids.name')
    def _summary_voucher_line(self):
        for voucher in self:
            voucher.summary_description = ', '.join([line.name for line in voucher.line_ids])

    @api.depends('amount')
    def _compute_terbilang(self):
        for line in self:
            text = line._convert_num2words()
            line.terbilang = (text.replace('KOMA NOL',''))

    def _fetch_next_seq(self):
        return self.type.sequence_id.next_by_id()

    def _convert_num2words(self):
        #check_amount_in_words = currency.amount_to_text(math.floor(amount), lang='en', currency='')
        check_amount_in_words = (num2words(self.amount, lang='id') + ' ' + (self.currency_id.currency_unit_label or '')).upper()
        return check_amount_in_words
    
    def print_payment_voucher(self):
        line_ids = self.mapped('line_ids')
        if not line_ids:
            raise UserError(_('Nothing to print.'))
        return self.env.ref('aos_account_voucher.action_report_account_voucher').report_action(self)
    
    
    def attachment_voucher_view(self):
        self.ensure_one()
        domain = [
            ('res_model', '=', 'account.voucher'), ('res_id', 'in', self.ids)]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                        Documents are attached to the purchase order.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your property contract.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    @api.depends('move_id.line_ids.full_reconcile_id', 'move_id.line_ids.reconciled', 'move_id.line_ids.account_id.internal_type')
    def _check_paid(self):
        #self.paid = any([((line.account_id.internal_type, 'in', ('receivable', 'payable')) and line.reconciled) for line in self.move_id.line_ids])
        for voucher in self:
            if voucher.voucher_type == 'sale':
                account_id = voucher.payment_journal_id.inbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
            else:
                account_id = voucher.payment_journal_id.outbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
            
            voucher.paid = any([(line.account_id.reconcile and line.reconciled) for line in voucher.move_id.line_ids.filtered(lambda ml: ml.account_id == account_id)])
            if voucher.paid:
                voucher.state = 'posted'

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        return self.env.user.company_id.currency_id.id

    # @api.model
    # def _get_company(self):
    #     return self._context.get('company_id', self.env.user.company_id.id)

    @api.constrains('company_id', 'currency_id')
    def _check_company_id(self):
        for voucher in self:
            if not voucher.company_id:
                raise ValidationError(_("Missing Company"))
            if not voucher.currency_id:
                raise ValidationError(_("Missing Currency"))

    @api.depends('name', 'number')
    def name_get(self):
        return [(r.id, (r.number or _('Voucher'))) for r in self]

    @api.depends('payment_journal_id', 'company_id')
    def _get_journal_currency(self):
        self.currency_id = self.payment_journal_id.currency_id.id or self.company_id.currency_id.id

    @api.depends('tax_correction', 'line_ids.price_subtotal')
    def _compute_total(self):
        tax_calculation_rounding_method = self.env.user.company_id.tax_calculation_rounding_method
        for voucher in self:
            total = 0
            tax_amount = 0
            tax_lines_vals_merged = {}
            for line in voucher.line_ids:
                tax_info = line.tax_ids.compute_all(line.price_unit, voucher.currency_id, line.quantity, line.product_id, voucher.partner_id)
                if tax_calculation_rounding_method == 'round_globally':
                    total += tax_info.get('total_excluded', 0.0)
                    for t in tax_info.get('taxes', False):
                        key = (
                            t['id'],
                            t['account_id'],
                        )
                        if key not in tax_lines_vals_merged:
                            tax_lines_vals_merged[key] = t.get('amount', 0.0)
                        else:
                            tax_lines_vals_merged[key] += t.get('amount', 0.0)
                else:
                    total += tax_info.get('total_included', 0.0)
                    tax_amount += sum([t.get('amount', 0.0) for t in tax_info.get('taxes', False)])
            if tax_calculation_rounding_method == 'round_globally':
                tax_amount = sum([voucher.currency_id.round(t) for t in tax_lines_vals_merged.values()])
                voucher.amount = total + tax_amount + voucher.tax_correction
            else:
                voucher.amount = total + voucher.tax_correction
            voucher.tax_amount = tax_amount

    @api.onchange('date')
    def onchange_date(self):
        self.account_date = self.date

    @api.onchange('voucher_type', 'partner_id', 'pay_now', 'journal_id', 'payment_journal_id')
    def onchange_partner_id(self):
        #pay_journal_domain = [('type', 'in', ['cash', 'bank'])]
        pay_journal_domain = [('is_voucher', '=', True)]
        # print ('====self.journal_id.currency_id===',self.journal_id.currency_id)
        # if self.payment_journal_id.currency_id:
        #     self.currency_id = self.payment_journal_id.currency_id
        domain = [
            ('company_id', '=', self.company_id.id),
        ]
        if self.partner_id:
            if self.pay_now == 'pay_now':
                self.account_id = self.payment_journal_id.default_account_id \
                    if self.voucher_type == 'sale' else self.payment_journal_id.default_account_id
            else:
                self.account_id = self.partner_id.property_account_receivable_id \
                    if self.voucher_type == 'sale' else self.partner_id.property_account_payable_id  
        else:            
            if self.pay_now == 'pay_now':
                self.account_id = self.payment_journal_id.default_account_id \
                    if self.voucher_type == 'sale' else self.payment_journal_id.default_account_id
            else:
                self.account_id = self.env['account.account'].search(domain+[('internal_type', '=', 'receivable' if self.voucher_type == 'sale' else 'payable')], limit=1)
            if self.voucher_type == 'purchase':
                self.journal_id = self.env['account.journal'].search(domain+[('type','=','purchase')], limit=1)
                pay_journal_domain.append(('available_payment_method_ids', '!=', False))
            else:
                self.journal_id = self.env['account.journal'].search(domain+[('type','=','sale')], limit=1)
                pay_journal_domain.append(('available_payment_method_ids', '!=', False))
        return {'domain': {'payment_journal_id': pay_journal_domain}}

    # @api.onchange('line_ids')
    # def _onchange_line_ids(self):
    #     if not self.line_ids:
    #         return
    #     for line in self.line_ids:
    #         line.account_analytic_id = self.account_analytic_id and self.account_analytic_id.id

#     @api.onchange('partner_id', 'pay_now', 'journal_id')
#     def onchange_partner_id(self):
#         #print "==onchange_partner_id==",self.pay_now,self.voucher_type
#         if self.pay_now == 'pay_now':
#             if self.journal_id.type in ('sale','purchase'):
#                 liq_journal = self.env['account.journal'].search([('type','not in',['sale','purchase'])], limit=1)
#                 self.account_id = liq_journal.default_account_id \
#                     if self.voucher_type == 'sale' else liq_journal.default_account_id
#             else:
#                 self.account_id = self.journal_id.default_account_id \
#                     if self.voucher_type == 'sale' else self.journal_id.default_account_id
#         else:
#             if self.partner_id:
#                 self.account_id = self.partner_id.property_account_receivable_id \
#                     if self.voucher_type == 'sale' else self.partner_id.property_account_payable_id
#             elif self.journal_id.type not in ('sale','purchase'):
#                 self.account_id = False
#             else:
#                 self.account_id = self.journal_id.default_account_id \
#                     if self.voucher_type == 'sale' else self.journal_id.default_account_id

    def confirm_voucher(self):
        #print ('===confirm_voucher==')
        if self.number == 'New':
            self.number = self._fetch_next_seq()
        self.write({'state': 'confirm'})

    def proforma_voucher(self):
        self.action_move_line_create()
        if self.voucher_type == 'sale':
            account_id = self.payment_journal_id.inbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
        else:
            account_id = self.payment_journal_id.outbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
        if account_id != self.account_id:
            self.write({'state': 'posted'})
        else:
            self.write({'state': 'posted'})

    def action_cancel_draft(self):
        self.write({'state': 'draft'})

    def cancel_voucher(self):
        for voucher in self:
            voucher.move_id.button_draft()
            voucher.move_id.button_cancel()
            voucher.move_id.with_context(force_delete=True).unlink()
        self.write({'state': 'cancel', 'move_id': False})

    def unlink(self):
        for voucher in self:
            if voucher.state not in ('draft', 'cancel'):
                raise UserError(_('Cannot delete voucher(s) which are already opened or paid.'))
        return super(AccountVoucher, self).unlink()


    # def first_move_line_get(self, move_id, company_currency, current_currency):
    #     #print ("FIRST MOVE LINE")
    #     debit = credit = 0.0
    #     if self.voucher_type == 'purchase':
    #         credit = self._convert(abs(self.amount))
    #     elif self.voucher_type == 'sale':
    #         debit = self._convert(abs(self.amount))
    #     if debit < 0.0: debit = 0.0
    #     if credit < 0.0: credit = 0.0
    #     #print("@@@@@@@@",debit,credit)
    #     sign = debit - credit < 0 and -1 or 1
    #     #set the first line of the voucher
    #     if self.voucher_type == 'sale':
    #         account_id = self.payment_journal_id.inbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
    #     else:
    #         account_id = self.payment_journal_id.outbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
    #     #print ("DOOOR")
    #     move_line = {
    #         'name': self.name or '/',
    #         'debit': debit,
    #         'credit': credit,
    #         'account_id': account_id.id if account_id else self.account_id.id,
    #         'move_id': move_id,
    #         'journal_id': self.payment_journal_id.id if self.pay_now == 'pay_now' else self.journal_id.id,
    #         'partner_id': self.partner_id.commercial_partner_id.id,
    #         'currency_id': company_currency != current_currency and current_currency or False,
    #         'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
    #             if company_currency != current_currency else 0.0),
    #         'date': self.account_date,
    #         'date_maturity': self.date_due,
    #     }
    #     #print("TOTAL",move_line)
    #     return move_line

    def first_move_line_get(self, move_id, company_currency, current_currency):
        print ("FIRST MOVE LINE",move_id, company_currency, current_currency)
        debit = credit = 0.0
        if self.voucher_type == 'purchase':
            credit = self._convert(abs(self.amount))
        elif self.voucher_type == 'sale':
            debit = self._convert(abs(self.amount))
        if debit < 0.0: debit = 0.0
        if credit < 0.0: credit = 0.0
        print("@@@@@@@@",debit,credit)
        sign = debit - credit < 0 and -1 or 1
        #print ("FIRST MOVE LINE",debit,credit)
        #set the first line of the voucher
        if self.voucher_type == 'sale':
            account_id = self.payment_journal_id.inbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
        else:
            account_id = self.payment_journal_id.outbound_payment_method_line_ids.filtered(lambda j: j.payment_method_id.name == 'Manual').mapped('payment_account_id')
        print ("DOOOR",account_id)
        move_line = {
            'name': self.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': account_id.id if account_id else self.account_id.id,
            'move_id': move_id,
            'journal_id': self.payment_journal_id.id if self.pay_now == 'pay_now' else self.journal_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
                if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.date_due,
        }
        print("TOTAL",move_line)
        return move_line


    def account_move_get(self):
        # if self.number:
        #     name = self.number
        # elif self.pay_now == 'pay_now':
        #     if self.payment_journal_id.id:
        #         if not self.payment_journal_id.sequence_id.active:
        #             raise UserError(_('Please activate the sequence of selected journal !'))
        #     name = self.payment_journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        # elif self.pay_now == 'pay_later':
        #     if self.journal_id.sequence_id:
        #         if not self.journal_id.sequence_id.active:
        #             raise UserError(_('Please activate the sequence of selected journal !'))
        #     name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        # else:
        #     raise UserError(_('Please define a sequence on the journal.'))
 
        move = {
            # 'name': '/',
            'journal_id': self.payment_journal_id.id if self.pay_now == 'pay_now' else self.journal_id.id,
            'narration': self.narration or '',
            'date': self.account_date,
            'ref': self.reference or '',
        }
        print ('===s===',move)
        return move


    def _convert(self, amount):
        '''
        This function convert the amount given in company currency. It takes either the rate in the voucher (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.
        :param amount: float. The amount to convert
        :param voucher: id of the voucher on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the voucher date
            field in order to select the good rate to use.
        :return: the amount in the currency of the voucher's company
        :rtype: float
        '''
        for voucher in self:
            #print ('_convert_', voucher.currency_id.rounding)
            return voucher.currency_id.with_context(rounding=voucher.currency_id.rounding)._convert(amount, voucher.company_id.currency_id, voucher.company_id, voucher.account_date, round=True)


#     def voucher_pay_now_payment_create(self):
#         if self.voucher_type == 'sale':
#             payment_methods = self.journal_id.inbound_payment_method_ids
#             payment_type = 'inbound'
#             partner_type = 'customer'
#             sequence_code = 'account.payment.customer.invoice'
#         else:
#             payment_methods = self.journal_id.outbound_payment_method_ids
#             payment_type = 'outbound'
#             partner_type = 'supplier'
#             sequence_code = 'account.payment.supplier.invoice'
#         return {
#             'payment_type': payment_type,
#             'payment_method_id': payment_methods and payment_methods[0].id or False,
#             'partner_type': partner_type,
#             'partner_id': self.partner_id.commercial_partner_id.id,
#             'amount': self.amount,
#             'currency_id': self.currency_id.id,
#             'payment_date': self.date,
#             'journal_id': self.payment_journal_id.id,
#             'communication': self.name,
#         }
    
    # def _prepare_voucher_move_line(self, line, amount, move_id, company_currency, current_currency):
    #     line_subtotal = 0#line.price_subtotal
    #     # if self.voucher_type == 'sale':
    #     #     line_subtotal = -1 * line.price_subtotal
    #     # convert the amount set on the voucher line into the currency of the voucher's company
    #     #amount = self._convert(line.price_unit*line.quantity)
    #     #===================================================================
    #     # ALLOW DEBIT AND CREDIT BASED ON MINUS OR PLUS
    #     #===================================================================
    #     if (self.voucher_type == 'sale' and amount > 0.0) or (self.voucher_type == 'purchase' and amount < 0.0):
    #         debit = 0.0
    #         credit = abs(amount)
    #         line_subtotal = self._convert(amount)
    #     elif (self.voucher_type == 'sale' and amount < 0.0) or (self.voucher_type == 'purchase' or amount > 0.0):
    #         debit = abs(amount)
    #         credit = 0.0
    #         line_subtotal = self._convert(amount)
    #     if not line.account_id:
    #         raise UserError(_("In order to Validate Voucher you must add account for detail items"))
    #     move_line = {
    #         'journal_id': self.journal_id.id,
    #         'name': line.name or '/',
    #         'account_id': line.account_id.id,
    #         'move_id': move_id,
    #         'quantity': line.quantity,
    #         'product_id': line.product_id.id,
    #         'partner_id': self.partner_id.commercial_partner_id.id,
    #         'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
    #         'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
    #         #===================================================================     
    #         'credit': abs(amount) if credit > 0.0 else 0.0,
    #         'debit': abs(amount) if debit > 0.0 else 0.0,
    #         #===================================================================
    #         'date': self.account_date,
    #         'tax_ids': [(4,t.id) for t in line.tax_ids],
    #         'amount_currency': line_subtotal if current_currency != company_currency else line_subtotal,
    #         'currency_id': company_currency != current_currency and current_currency or False,
    #         'payment_id': self._context.get('payment_id'),
    #     }
    #     #print ('==_prepare_voucher_move_line=',move_line)
    #     return move_line


    def _prepare_voucher_move_line(self, line, amount, move_id, company_currency, current_currency):
        line_subtotal = 0#line.price_subtotal
        # if self.voucher_type == 'sale':
        #     line_subtotal = -1 * line.price_subtotal
        # convert the amount set on the voucher line into the currency of the voucher's company
        #amount = self._convert(line.price_unit*line.quantity)
        #===================================================================
        # ALLOW DEBIT AND CREDIT BASED ON MINUS OR PLUS
        #===================================================================
        if (self.voucher_type == 'sale' and amount > 0.0) or (self.voucher_type == 'purchase' and amount < 0.0):
            debit = 0.0
            credit = abs(amount)
            line_subtotal = self._convert(amount)
        elif (self.voucher_type == 'sale' and amount < 0.0) or (self.voucher_type == 'purchase' or amount > 0.0):
            debit = abs(amount)
            credit = 0.0
            line_subtotal = self._convert(amount)
        if not line.account_id:
            raise UserError(_("In order to Validate Voucher you must add account for detail items"))
        move_line = {
            'journal_id': self.journal_id.id,
            'name': line.name or '/',
            'account_id': line.account_id.id,
            'move_id': move_id,
            'quantity': line.quantity,
            'product_id': line.product_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
            'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
            #===================================================================     
            'credit': abs(amount) if credit > 0.0 else 0.0,
            'debit': abs(amount) if debit > 0.0 else 0.0,
            #===================================================================
            'date': self.account_date,
            'tax_ids': [(4,t.id) for t in line.tax_ids],
            'amount_currency': line_subtotal if current_currency != company_currency else line_subtotal,
            'currency_id': company_currency != current_currency and current_currency or False,
            'payment_id': self._context.get('payment_id'),
        }
        # print ('==_prepare_voucher_move_line=',move_line)
        return move_line

    def _prepare_voucher_lines(self, move_id, company_currency, current_currency, line_subtotal, line, debit, credit):
        move_line = {
            'journal_id': self.journal_id.id,
            'name': line.name or '/',
            'account_id': line.account_id.id,
            'move_id': move_id,
            'partner_id': line.partner_id.id if line.partner_id else self.partner_id.id,
            'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
            'quantity': 1,
            'debit': debit,#abs(amount) if self.voucher_type == 'sale' and amount > 0 else 0.0,
            'credit': credit,#abs(amount) if self.voucher_type == 'purchase' and amount < 0 else 0.0,
            'date': self.account_date,
            'tax_ids': [(6, 0, line.tax_ids.ids)],
            'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
            'currency_id': company_currency != current_currency and current_currency or False,
            'payment_id': self._context.get('payment_id'),
        }
        return move_line
       
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        for line in self.line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            line_subtotal = line.price_subtotal
            if self.voucher_type == 'sale':
                line_subtotal = -1 * line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            #amount = self._convert_amount(line.price_unit*line.quantity)
            amount = self._convert(line.price_unit * line.quantity)
            if self.voucher_type == 'purchase':
                debit = abs(amount) if amount > 0 else 0.0
                credit = abs(amount) if amount < 0 else 0.0
            else:
                debit = abs(amount) if amount < 0 else 0.0
                credit = abs(amount) if amount > 0 else 0.0

            #print ('==amount==',amount)
            # move_line = {
            #     'journal_id': self.journal_id.id,
            #     'name': line.name or '/',
            #     'account_id': line.account_id.id,
            #     'move_id': move_id,
            #     'partner_id': line.partner_id.id if line.partner_id else self.partner_id.id,
            #     'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
            #     'quantity': 1,
            #     'debit': debit,#abs(amount) if self.voucher_type == 'sale' and amount > 0 else 0.0,
            #     'credit': credit,#abs(amount) if self.voucher_type == 'purchase' and amount < 0 else 0.0,
            #     'date': self.account_date,
            #     'tax_ids': [(6, 0, line.tax_ids.ids)],
            #     'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
            #     'currency_id': company_currency != current_currency and current_currency or False,
            #     'payment_id': self._context.get('payment_id'),
            # }
            move_line = self._prepare_voucher_lines(move_id, company_currency, current_currency, line_subtotal, line, debit, credit)
            #print ('===voucher_move_line_create===',line.partner_id,move_line)
            self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
        return line_total
    
    # def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
    #     '''
    #     Create one account move line, on the given account move, per voucher line where amount is not 0.0.
    #     It returns Tuple with tot_line what is total of difference between debit and credit and
    #     a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

    #     :param voucher_id: Voucher id what we are working with
    #     :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
    #     :param move_id: Account move wher those lines will be joined.
    #     :param company_currency: id of currency of the company to which the voucher belong
    #     :param current_currency: id of currency of the voucher
    #     :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
    #     :rtype: tuple(float, list of int)
    #     '''
    #     for line in self.line_ids:
    #         #create one move line per voucher line where amount is not 0.0
    #         if not line.price_subtotal:
    #             continue
    #         line_subtotal = line.price_subtotal
    #         if self.voucher_type == 'sale':
    #             line_subtotal = -1 * line.price_subtotal
    #         # convert the amount set on the voucher line into the currency of the voucher's company
    #         # this calls res_curreny.compute() with the right context,
    #         # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
    #         #amount = self._convert_amount(line.price_unit*line.quantity)
    #         amount = self._convert(line.price_unit * line.quantity)
    #         move_line = {
    #             'journal_id': self.journal_id.id,
    #             'name': line.name or '/',
    #             'account_id': line.account_id.id,
    #             'move_id': move_id,
    #             'partner_id': self.partner_id.commercial_partner_id.id,
    #             'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
    #             'quantity': 1,
    #             'credit': abs(amount) if self.voucher_type == 'sale' else 0.0,
    #             'debit': abs(amount) if self.voucher_type == 'purchase' else 0.0,
    #             'date': self.account_date,
    #             #'tax_ids': [(4,t.id) for t in line.tax_ids],
    #             'tax_ids': [(6, 0, line.tax_ids.ids)],
    #             'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
    #             'currency_id': company_currency != current_currency and current_currency or False,
    #             'payment_id': self._context.get('payment_id'),
    #         }
    #         #print ('===voucher_move_line_create===',move_line)
    #         self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
    #     return line_total
    
#     def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
#         '''
#         Create one account move line, on the given account move, per voucher line where amount is not 0.0.
#         It returns Tuple with tot_line what is total of difference between debit and credit and
#         a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).
 
#         :param voucher_id: Voucher id what we are working with
#         :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
#         :param move_id: Account move wher those lines will be joined.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
#         :rtype: tuple(float, list of int)
#         '''
#         total_line = 0
#         for line in self.line_ids:
#             #create one move line per voucher line where amount is not 0.0
#             if not line.price_subtotal:
#                 continue
# #             line_subtotal = line.price_subtotal
# #             if self.voucher_type == 'sale':
# #                 line_subtotal = -1 * line.price_subtotal
# #             # convert the amount set on the voucher line into the currency of the voucher's company
#             amount = self._convert(line.price_unit * line.quantity)
#             #print ('===force_rate===',line_total,self._context,amount,line.price_unit)
# #             #===================================================================
# #             # ALLOW DEBIT AND CREDIT BASED ON MINUS OR PLUS
# #             #===================================================================
# #             if (self.voucher_type == 'sale' and amount > 0.0) or (self.voucher_type == 'purchase' and amount < 0.0):
# #                 debit = 0.0
# #                 credit = abs(amount)
# #             elif (self.voucher_type == 'sale' and amount < 0.0) or (self.voucher_type == 'purchase' or amount > 0.0):
# #                 debit = abs(amount)
# #                 credit = 0.0
#             #===================================================================
#             move_line = self._prepare_voucher_move_line(line, amount, move_id, company_currency, current_currency) 
#             total_line += amount
# #             move_line = {
# #                 'journal_id': self.journal_id.id,
# #                 'name': line.name or '/',
# #                 'account_id': line.account_id.id,
# #                 'move_id': move_id,
# #                 'quantity': line.quantity,
# #                 'product_id': line.product_id.id,
# #                 'partner_id': self.partner_id.commercial_partner_id.id,
# #                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
# #                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
# #                 #===================================================================     
# #                 'credit': abs(amount) if credit > 0.0 else 0.0,
# #                 'debit': abs(amount) if debit > 0.0 else 0.0,
# #                 #===================================================================
# #                 'date': self.account_date,
# #                 'tax_ids': [(4,t.id) for t in line.tax_ids],
# #                 'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
# #                 'currency_id': company_currency != current_currency and current_currency or False,
# #                 'payment_id': self._context.get('payment_id'),
# #             }
#             # Create one line per tax and fix debit-credit for the move line if there are tax included
#             if (line.tax_ids):
#                 tax_group = line.tax_ids.compute_all(line.price_unit, line.currency_id, line.quantity, line.product_id, self.partner_id)
#                 #print ('==tax_group=',tax_group['total_excluded'])
#                 if move_line['debit']: move_line['debit'] = abs(tax_group['total_excluded'])
#                 if move_line['credit']: move_line['credit'] = abs(tax_group['total_excluded'])
#                 for tax_vals in tax_group['taxes']:
#                     if tax_vals['amount']:
#                         #print ('===s==1',tax_vals['amount'],move_line['debit'])
#                         tax = self.env['account.tax'].browse([tax_vals['id']])
#                         account_id = tax_vals['account_id']
#                         #if not account_id: account_id = line.account_id.id
#                         temp = {
#                             'account_id': account_id,
#                             'name': line.name + ' ' + tax_vals['name'],
#                             'tax_line_id': tax_vals['id'],
#                             'move_id': move_id,
#                             'date': self.account_date,
#                             'partner_id': self.partner_id.id,
#                             'debit': abs(tax_vals['amount']) if tax_vals['amount'] > 0 else 0.0,
#                             'credit': abs(tax_vals['amount']) if tax_vals['amount'] < 0 else 0.0,
#                             'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                         }
#                         if company_currency != current_currency:
#                             ctx = {}
#                             if self.account_date:
#                                 ctx['date'] = self.account_date
#                             temp['currency_id'] = current_currency.id
#                             temp['amount_currency'] = company_currency._convert(tax_vals['amount'], current_currency, line.company_id, self.account_date or fields.Date.today(), round=True)
#                         #print ('==voucher_move_line_create==TAX===',temp)
#                         self.env['account.move.line'].create(temp)
#             #print ('==voucher_move_line_create==LINE===',move_line)
#             self.env['account.move.line'].create(move_line)
#         return total_line
        

#     def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
#         '''
#         Create one account move line, on the given account move, per voucher line where amount is not 0.0.
#         It returns Tuple with tot_line what is total of difference between debit and credit and
#         a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).
#  
#         :param voucher_id: Voucher id what we are working with
#         :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
#         :param move_id: Account move wher those lines will be joined.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
#         :rtype: tuple(float, list of int)
#         '''
#         for line in self.line_ids:
#             #create one move line per voucher line where amount is not 0.0
#             if not line.price_subtotal:
#                 continue
#             line_subtotal = line.price_subtotal
#             if self.voucher_type == 'sale':
#                 line_subtotal = -1 * line.price_subtotal
#             # convert the amount set on the voucher line into the currency of the voucher's company
#             amount = self._convert(line.price_unit*line.quantity)
#             #===================================================================
#             # ALLOW DEBIT AND CREDIT BASED ON MINUS OR PLUS
#             #===================================================================
#             if (self.voucher_type == 'sale' and amount > 0.0) or (self.voucher_type == 'purchase' and amount < 0.0):
#                 debit = 0.0
#                 credit = abs(amount)
#             elif (self.voucher_type == 'sale' and amount < 0.0) or (self.voucher_type == 'purchase' or amount > 0.0):
#                 debit = abs(amount)
#                 credit = 0.0
#             #===================================================================            
#             move_line = {
#                 'journal_id': self.journal_id.id,
#                 'name': line.name or '/',
#                 'account_id': line.account_id.id,
#                 'move_id': move_id,
#                 'quantity': line.quantity,
#                 'product_id': line.product_id.id,
#                 'partner_id': self.partner_id.commercial_partner_id.id,
#                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 #===================================================================     
#                 'credit': abs(amount) if credit > 0.0 else 0.0,
#                 'debit': abs(amount) if debit > 0.0 else 0.0,
#                 #===================================================================
#                 'date': self.account_date,
#                 'tax_ids': [(4,t.id) for t in line.tax_ids],
#                 'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
#                 'currency_id': company_currency != current_currency and current_currency or False,
#                 'payment_id': self._context.get('payment_id'),
#             }
#             # Create one line per tax and fix debit-credit for the move line if there are tax included
#             if (line.tax_ids):
#                 tax_group = line.tax_ids.compute_all(line.price_unit, line.currency_id, line.quantity, line.product_id, self.partner_id)
#                 if move_line['debit']: move_line['debit'] = tax_group['total_excluded']
#                 if move_line['credit']: move_line['credit'] = tax_group['total_excluded']
#                 for tax_vals in tax_group['taxes']:
#                     if tax_vals['amount']:
#                         tax = self.env['account.tax'].browse([tax_vals['id']])
#                         account_id = (amount > 0 and tax_vals['account_id'] or tax_vals['refund_account_id'])
#                         if not account_id: account_id = line.account_id.id
#                         temp = {
#                             'account_id': account_id,
#                             'name': line.name + ' ' + tax_vals['name'],
#                             'tax_line_id': tax_vals['id'],
#                             'move_id': move_id,
#                             'date': self.account_date,
#                             'partner_id': self.partner_id.id,
#                             'debit': self.voucher_type != 'sale' and tax_vals['amount'] or 0.0,
#                             'credit': self.voucher_type == 'sale' and tax_vals['amount'] or 0.0,
#                             'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                         }
#                         if company_currency != current_currency:
#                             ctx = {}
#                             if self.account_date:
#                                 ctx['date'] = self.account_date
#                             temp['currency_id'] = current_currency.id
#                             temp['amount_currency'] = company_currency._convert(tax_vals['amount'], current_currency, line.company_id, self.account_date or fields.Date.today(), round=True)
#                         self.env['account.move.line'].create(temp)
#  
#             self.env['account.move.line'].create(move_line)
#         return line_total
     

    # Get Num2words For total
    def _get_num2words(self,amount):
        return num2words(int(amount),lang='id')

    def action_move_line_create(self):
        print (''' PAY NOW IS DIRECT JOURNAL NON ACTIVE RECONCILED BEHAVIOUR''')
        #Confirm the vouchers given in ids and create the journal entries for each of them
        for voucher in self:
            print ("yyyyyy",voucher.balance)
            if self.user_has_groups('aos_account_voucher.account_voucher_crosscheck_validate') and (voucher.balance != 0.0):
                raise ValidationError(_('The amount is not balance yet!'))
            local_context = dict(self._context, company_id=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = voucher.journal_id.company_id.currency_id.id
            current_currency = voucher.currency_id.id or company_currency
            # we select the context to use accordingly if it's a multicurrency case or not
            # But for the operations made by _convert, we always need to give the date in the context
            ctx = local_context.copy()
            ctx['date'] = voucher.account_date
            ctx['check_move_validity'] = False
            print ('==# Create the account move record.')
            move = self.env['account.move'].create(voucher.account_move_get())
            # Get the name of the account_move just created
            print ('>==Create the first line of the voucher===>')
            move_line = self.env['account.move.line'].with_context(ctx).create(voucher.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency))
            total = move_line.debit - move_line.credit
            print ('===line_total===',total,move_line.debit,move_line.credit)
            if voucher.voucher_type == 'sale':
                total = total - voucher._convert(voucher.tax_amount)
            elif voucher.voucher_type == 'purchase':
                total = total + voucher._convert(voucher.tax_amount)
            #print ('==total==',voucher.voucher_type,total,voucher.tax_amount)
            # Create one move line per voucher line where amount is not 0.0
            vline_total = voucher.with_context(ctx).voucher_move_line_create(abs(total), move.id, company_currency, current_currency)
            # Create a payment to allow the reconciliation when pay_now = 'pay_now'.
#===============================================================================
#             if voucher.pay_now == 'pay_now':
#                 payment_id = (self.env['account.payment']
#                     .with_context(force_counterpart_account=voucher.account_id.id)
#                     .create(voucher.voucher_pay_now_payment_create()))
#                 payment_id.post()
# 
#                 # Reconcile the receipt with the payment
#                 lines_to_reconcile = (payment_id.move_line_ids + move.line_ids).filtered(lambda l: l.account_id == voucher.account_id)
#                 lines_to_reconcile.reconcile()
#===============================================================================
            # Add tax correction to move line if any tax correction specified
            if voucher.tax_correction != 0.0:
                tax_move_line = self.env['account.move.line'].search([('move_id', '=', move.id), ('tax_line_id', '!=', False)], limit=1)
                #print ('==tax_move_line==',voucher.tax_correction,tax_move_line.debit,tax_move_line.credit)
                if len(tax_move_line):
                    tax_move_line.write({
                        'debit': tax_move_line.debit + voucher.tax_correction if tax_move_line.debit > 0 else 0,
                        'credit': tax_move_line.credit + voucher.tax_correction if tax_move_line.credit > 0 else 0
                    })
 
            # We post the voucher.
            #print ('=action_move_line_create=11=',voucher.voucher_type,vline_total,total,(vline_total + total))
            if voucher.voucher_type == 'purchase' and (vline_total + total):
                if (vline_total + total) < 0 and move_line.credit:
                    move_line.credit = move_line.credit + (vline_total + total)
                else:
                    move_line.debit = move_line.currency_id.round(move_line.debit + (vline_total + total))
                    # move_line.debit = move_line.debit + (vline_total + total)
            elif voucher.voucher_type == 'sale' and (vline_total - total):
                if (vline_total - total) < 0 and move_line.debit:
                    move_line.debit = move_line.debit + (vline_total - total)
                else:
                    move_line.credit = move_line.credit + (vline_total - total)
            move.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True)
            move.action_post()
            # move._post(soft=True)
            voucher.write({
                'move_id': move.id,
                #'state': 'posted',
                #'number': move.name
            })
            #print ('=action_move_line_create=22=',line_total)
        return True

#     def action_move_line_create(self):
#         ''' PAY NOW IS DIRECT JOURNAL NON ACTIVE RECONCILED BEHAVIOUR
#         Confirm the vouchers given in ids and create the journal entries for each of them
#         '''
#         for voucher in self:
#             #print ("yyyyyy",voucher.balance)
#             if (voucher.balance != 0.0):
#                 raise ValidationError(_('The amount is not balance yet!'))
#             local_context = dict(self._context, company_id=voucher.journal_id.company_id.id)
#             if voucher.move_id:
#                 continue
#             company_currency = voucher.journal_id.company_id.currency_id.id
#             current_currency = voucher.currency_id.id or company_currency
#             # we select the context to use accordingly if it's a multicurrency case or not
#             # But for the operations made by _convert, we always need to give the date in the context
#             ctx = local_context.copy()
#             ctx['date'] = voucher.account_date
#             ctx['check_move_validity'] = False
#             # Create the account move record.
#             move = self.env['account.move'].create(voucher.account_move_get())
#             # Get the name of the account_move just created
#             # Create the first line of the voucher
#             move_line = self.env['account.move.line'].with_context(ctx).create(voucher.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency))
#             total = move_line.debit - move_line.credit
#             #print ('===line_total===',total,move_line.debit,move_line.credit)
#             if voucher.voucher_type == 'sale':
#                 total = total - voucher._convert(voucher.tax_amount)
#             elif voucher.voucher_type == 'purchase':
#                 total = total + voucher._convert(voucher.tax_amount)
#             #print ('==total==',voucher.voucher_type,total,voucher.tax_amount)
#             # Create one move line per voucher line where amount is not 0.0
#             vline_total = voucher.with_context(ctx).voucher_move_line_create(abs(total), move.id, company_currency, current_currency)
#             # Create a payment to allow the reconciliation when pay_now = 'pay_now'.
# #===============================================================================
# #             if voucher.pay_now == 'pay_now':
# #                 payment_id = (self.env['account.payment']
# #                     .with_context(force_counterpart_account=voucher.account_id.id)
# #                     .create(voucher.voucher_pay_now_payment_create()))
# #                 payment_id.post()
# # 
# #                 # Reconcile the receipt with the payment
# #                 lines_to_reconcile = (payment_id.move_line_ids + move.line_ids).filtered(lambda l: l.account_id == voucher.account_id)
# #                 lines_to_reconcile.reconcile()
# #===============================================================================
#             # Add tax correction to move line if any tax correction specified
#             if voucher.tax_correction != 0.0:
#                 tax_move_line = self.env['account.move.line'].search([('move_id', '=', move.id), ('tax_line_id', '!=', False)], limit=1)
#                 #print ('==tax_move_line==',voucher.tax_correction,tax_move_line.debit,tax_move_line.credit)
#                 if len(tax_move_line):
#                     tax_move_line.write({
#                         'debit': tax_move_line.debit + voucher.tax_correction if tax_move_line.debit > 0 else 0,
#                         'credit': tax_move_line.credit + voucher.tax_correction if tax_move_line.credit > 0 else 0
#                     })
 
#             # We post the voucher.
#             #print ('=action_move_line_create=11=',voucher.voucher_type,vline_total,total,(vline_total + total))
#             if voucher.voucher_type == 'purchase' and (vline_total + total):
#                 if (vline_total + total) < 0 and move_line.credit:
#                     move_line.credit = move_line.credit + (vline_total + total)
#                 else:
#                     move_line.debit = move_line.currency_id.round(move_line.debit + (vline_total + total))
#                     # move_line.debit = move_line.debit + (vline_total + total)
#             elif voucher.voucher_type == 'sale' and (vline_total - total):
#                 if (vline_total - total) < 0 and move_line.debit:
#                     move_line.debit = move_line.debit + (vline_total - total)
#                 else:
#                     move_line.credit = move_line.credit + (vline_total - total)
#             move._post(soft=True)
            
#             voucher.write({
#                 'move_id': move.id,
#                 #'state': 'posted',
#                 #'number': move.name
#             })
#             #print ('=action_move_line_create=22=',line_total)
#         return True
    
    
#===============================================================================
#     ASLI
#===============================================================================
#     @api.multi
#     def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
#         '''
#         Create one account move line, on the given account move, per voucher line where amount is not 0.0.
#         It returns Tuple with tot_line what is total of difference between debit and credit and
#         a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).
# 
#         :param voucher_id: Voucher id what we are working with
#         :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
#         :param move_id: Account move wher those lines will be joined.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
#         :rtype: tuple(float, list of int)
#         '''
#         tax_calculation_rounding_method = self.env.user.company_id.tax_calculation_rounding_method
#         tax_lines_vals = []
#         for line in self.line_ids:
#             #create one move line per voucher line where amount is not 0.0
#             if not line.price_subtotal:
#                 continue
#             line_subtotal = line.price_subtotal
#             if self.voucher_type == 'sale':
#                 line_subtotal = -1 * line.price_subtotal
#             # convert the amount set on the voucher line into the currency of the voucher's company
#             amount = self._convert(line.price_unit*line.quantity)
#             move_line = {
#                 'journal_id': self.journal_id.id,
#                 'name': line.name or '/',
#                 'account_id': line.account_id.id,
#                 'move_id': move_id,
#                 'quantity': line.quantity,
#                 'product_id': line.product_id.id,
#                 'partner_id': self.partner_id.commercial_partner_id.id,
#                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                 'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
#                 'credit': abs(amount) if self.voucher_type == 'sale' else 0.0,
#                 'debit': abs(amount) if self.voucher_type == 'purchase' else 0.0,
#                 'date': self.account_date,
#                 'tax_ids': [(4,t.id) for t in line.tax_ids],
#                 'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
#                 'currency_id': company_currency != current_currency and current_currency or False,
#                 'payment_id': self._context.get('payment_id'),
#             }
#             # Create one line per tax and fix debit-credit for the move line if there are tax included
#             if (line.tax_ids and tax_calculation_rounding_method == 'round_per_line'):
#                 tax_group = line.tax_ids.compute_all(self._convert(line.price_unit), self.company_id.currency_id, line.quantity, line.product_id, self.partner_id)
#                 if move_line['debit']: move_line['debit'] = tax_group['total_excluded']
#                 if move_line['credit']: move_line['credit'] = tax_group['total_excluded']
#                 Currency = self.env['res.currency']
#                 company_cur = Currency.browse(company_currency)
#                 current_cur = Currency.browse(current_currency)
#                 for tax_vals in tax_group['taxes']:
#                     if tax_vals['amount']:
#                         tax = self.env['account.tax'].browse([tax_vals['id']])
#                         account_id = (amount > 0 and tax_vals['account_id'] or tax_vals['refund_account_id'])
#                         if not account_id: account_id = line.account_id.id
#                         temp = {
#                             'account_id': account_id,
#                             'name': line.name + ' ' + tax_vals['name'],
#                             'tax_line_id': tax_vals['id'],
#                             'move_id': move_id,
#                             'date': self.account_date,
#                             'partner_id': self.partner_id.id,
#                             'debit': self.voucher_type != 'sale' and tax_vals['amount'] or 0.0,
#                             'credit': self.voucher_type == 'sale' and tax_vals['amount'] or 0.0,
#                             'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                         }
#                         if company_currency != current_currency:
#                             ctx = {}
#                             sign = temp['credit'] and -1 or 1
#                             amount_currency = company_cur._convert(tax_vals['amount'], current_cur, line.company_id,
#                                                  self.account_date or fields.Date.today(), round=True)
#                             if self.account_date:
#                                 ctx['date'] = self.account_date
#                             temp['currency_id'] = current_currency
#                             temp['amount_currency'] = sign * abs(amount_currency)
#                         self.env['account.move.line'].create(temp)
# 
#             # When global rounding is activated, we must wait until all tax lines are computed to
#             # merge them.
#             if tax_calculation_rounding_method == 'round_globally':
#                 # _apply_taxes modifies the dict move_line in place to account for included/excluded taxes
#                 tax_lines_vals += self.env['account.move.line'].with_context(round=False)._apply_taxes(
#                     move_line,
#                     move_line.get('debit', 0.0) - move_line.get('credit', 0.0)
#                 )
#                 # rounding False means the move_line's amount are not rounded
#                 currency = self.env['res.currency'].browse(company_currency)
#                 move_line['debit'] = currency.round(move_line['debit'])
#                 move_line['credit'] = currency.round(move_line['credit'])
#             self.env['account.move.line'].create(move_line)
# 
#         # When round globally is set, we merge the tax lines
#         if tax_calculation_rounding_method == 'round_globally':
#             tax_lines_vals_merged = {}
#             for tax_line_vals in tax_lines_vals:
#                 key = (
#                     tax_line_vals['tax_line_id'],
#                     tax_line_vals['account_id'],
#                     tax_line_vals['analytic_account_id'],
#                 )
#                 if key not in tax_lines_vals_merged:
#                     tax_lines_vals_merged[key] = tax_line_vals
#                 else:
#                     tax_lines_vals_merged[key]['debit'] += tax_line_vals['debit']
#                     tax_lines_vals_merged[key]['credit'] += tax_line_vals['credit']
#             currency = self.env['res.currency'].browse(company_currency)
#             for vals in tax_lines_vals_merged.values():
#                 vals['debit'] = currency.round(vals['debit'])
#                 vals['credit'] = currency.round(vals['credit'])
#                 self.env['account.move.line'].create(vals)
#         return line_total
# 
#     @api.multi
#     def action_move_line_create(self):
#         '''
#         Confirm the vouchers given in ids and create the journal entries for each of them
#         '''
#         for voucher in self:
#             local_context = dict(self._context, force_company=voucher.journal_id.company_id.id)
#             if voucher.move_id:
#                 continue
#             company_currency = voucher.journal_id.company_id.currency_id.id
#             current_currency = voucher.currency_id.id or company_currency
#             # we select the context to use accordingly if it's a multicurrency case or not
#             # But for the operations made by _convert, we always need to give the date in the context
#             ctx = local_context.copy()
#             ctx['date'] = voucher.account_date
#             ctx['check_move_validity'] = False
#             # Create the account move record.
#             move = self.env['account.move'].create(voucher.account_move_get())
#             # Get the name of the account_move just created
#             # Create the first line of the voucher
#             move_line = self.env['account.move.line'].with_context(ctx).create(voucher.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency))
#             line_total = move_line.debit - move_line.credit
#             if voucher.voucher_type == 'sale':
#                 line_total = line_total - voucher._convert(voucher.tax_amount)
#             elif voucher.voucher_type == 'purchase':
#                 line_total = line_total + voucher._convert(voucher.tax_amount)
#             # Create one move line per voucher line where amount is not 0.0
#             line_total = voucher.with_context(ctx).voucher_move_line_create(line_total, move.id, company_currency, current_currency)
# 
#             # Create a payment to allow the reconciliation when pay_now = 'pay_now'.
#             if voucher.pay_now == 'pay_now':
#                 payment_id = (self.env['account.payment']
#                     .with_context(force_counterpart_account=voucher.account_id.id)
#                     .create(voucher.voucher_pay_now_payment_create()))
#                 payment_id.post()
# 
#                 # Reconcile the receipt with the payment
#                 lines_to_reconcile = (payment_id.move_line_ids + move.line_ids).filtered(lambda l: l.account_id == voucher.account_id)
#                 lines_to_reconcile.reconcile()
# 
#             # Add tax correction to move line if any tax correction specified
#             if voucher.tax_correction != 0.0:
#                 tax_move_line = self.env['account.move.line'].search([('move_id', '=', move.id), ('tax_line_id', '!=', False)], limit=1)
#                 if len(tax_move_line):
#                     tax_move_line.write({'debit': tax_move_line.debit + voucher.tax_correction if tax_move_line.debit > 0 else 0,
#                         'credit': tax_move_line.credit + voucher.tax_correction if tax_move_line.credit > 0 else 0})
# 
#             # We post the voucher.
#             voucher.write({
#                 'move_id': move.id,
#                 'state': 'posted',
#                 'number': move.name
#             })
#             move.post()
#         return True

#     def _track_subtype(self, init_values):
#         self.ensure_one()
#         if 'state' in init_values:
#             return 'aos_account_voucher.mt_voucher_state_change'
#         return super(AccountVoucher, self)._track_subtype(init_values)
    
    
#     def _track_subtype(self, init_values):
#         # OVERRIDE to add custom subtype depending of the state.
#         self.ensure_one()
# 
#         if not self.is_invoice(include_receipts=True):
#             return super(AccountMove, self)._track_subtype(init_values)
# 
#         if 'invoice_payment_state' in init_values and self.invoice_payment_state == 'paid':
#             return self.env.ref('account.mt_invoice_paid')
#         elif 'state' in init_values and self.state == 'posted' and self.is_sale_document(include_receipts=True):
#             return self.env.ref('account.mt_invoice_validated')
#         return super(AccountMove, self)._track_subtype(init_values)


class AccountVoucherLine(models.Model):
    _name = 'account.voucher.line'
    _description = 'Accounting Voucher Line'
    _order = 'voucher_id, sequence, id'

    def _get_default_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    # def _get_default_analytic(self):
    #     print ("-_get_default_analytic--",self._origin.voucher_id)
    #     return ''
    
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(default=10,
        help="Gives the sequence of this line when displaying the voucher.")
    partner_id = fields.Many2one('res.partner', 'Partner')
    voucher_id = fields.Many2one('account.voucher', 'Voucher', required=1, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='set null', index=True)
    uom_id = fields.Many2one('uom.uom', default=_get_default_uom_id, string='Unit of Measure', required=True)
    account_id = fields.Many2one('account.account', string='Account',
        required=False, domain=[('deprecated', '=', False)],
        help="The income or expense account related to the selected product.", readonly=False)
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price', oldname='amount')
    price_subtotal = fields.Monetary(string='Amount',
        store=True, readonly=True, compute='_compute_subtotal')
    quantity = fields.Float(digits='Product Unit of Measure',
        required=True, default=1)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=False)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    company_id = fields.Many2one('res.company', related='voucher_id.company_id', string='Company', store=True, readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Tax', help="Only for tax excluded from price")
    currency_id = fields.Many2one('res.currency', related='voucher_id.currency_id', readonly=False, store=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=False, store=True)

    def unlink(self):
        for line in self:
            if line.voucher_id.state not in ('draft', 'cancel'):
                raise UserError(_('Cannot delete voucher(s) which are already posted.'))
        return super(AccountVoucherLine, self).unlink()

    @api.depends('price_unit', 'tax_ids', 'quantity', 'product_id', 'voucher_id.currency_id')
    def _compute_subtotal(self):        
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            #price_subtotal = line.quantity * line.price_unit
            taxes = line.tax_ids.compute_all(line.price_unit, line.voucher_id.currency_id, line.quantity, product=line.product_id, partner=line.voucher_id.partner_id)
            line.update({
                'price_subtotal': taxes['total_included'],
            })
            
    @api.onchange('product_id', 'voucher_id', 
            #'price_unit', 
            'company_id')
    def _onchange_line_details(self):
        if not self.voucher_id or not self.product_id:# or not self.voucher_id.partner_id:
            return
        onchange_res = self.product_id_change(
            self.product_id.id,
            self.voucher_id.partner_id.id,
            self.price_unit,
            self.company_id.id,
            self.voucher_id.currency_id.id,
            self.voucher_id.voucher_type)
        for fname, fvalue in onchange_res['value'].items():
            setattr(self, fname, fvalue)

    def _get_account(self, product, fpos, type):
        accounts = product.product_tmpl_id.get_product_accounts(fpos)
        if type == 'sale':
            return accounts['income']
        return accounts['expense']

    def product_id_change(self, product_id, partner_id=False, price_unit=False, company_id=None, currency_id=None, type=None):
        # TDE note: mix of old and new onchange badly written in 9, multi but does not use record set
        context = self._context
        company_id = company_id if company_id is not None else context.get('company_id', False)
        company = self.env['res.company'].browse(company_id)
        currency = self.env['res.currency'].browse(currency_id)
        #if not partner_id:
        #    raise UserError(_("You must first select a partner."))
        part = self.env['res.partner'].browse(partner_id)
        if not part:
            part = company.partner_id
        if part.lang:
            self = self.with_context(lang=part.lang)

        product = self.env['product.product'].browse(product_id)
        fpos = part.property_account_position_id
        account = self._get_account(product, fpos, type)
        values = {
            'name': product.partner_ref,
            'account_id': account.id,
        }

        if type == 'purchase':
            values['price_unit'] = price_unit or product.standard_price
            taxes = product.supplier_taxes_id or account.tax_ids
            if product.description_purchase:
                values['name'] += '\n' + product.description_purchase
        else:
            values['price_unit'] = price_unit or product.lst_price
            taxes = product.taxes_id or account.tax_ids
            if product.description_sale:
                values['name'] += '\n' + product.description_sale

        values['tax_ids'] = taxes.ids
        values['uom_id'] = product.uom_id.id
        #values['account_analytic_id'] = self.voucher_id.account_analytic_id.id
        if company and currency:
            if company.currency_id != currency:
                if type == 'purchase':
                    values['price_unit'] = price_unit or product.standard_price
                values['price_unit'] = values['price_unit'] * currency.rate

        return {'value': values, 'domain': {}}
    

    def _get_computed_account_analytic(self):
        self.ensure_one()
        self = self.with_company(self.voucher_id.journal_id.company_id)
        print ('===_get_computed_account_analytic===', self.voucher_id)
        return self.voucher_id.account_analytic_id and self.voucher_id.account_analytic_id.id

    @api.onchange('name')
    def _onchange_analytic(self):
        for line in self:
            if not line.name:
                continue
            line.account_analytic_id = line._get_computed_account_analytic()       

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Allows to force the destination account
    # for receivable/payable
    #
    # @override
    def _get_counterpart_move_line_vals(self, invoice=False):
        values = super(AccountPayment, self)._get_counterpart_move_line_vals(invoice)

        if self._context.get('force_counterpart_account'):
            values['account_id'] = self._context['force_counterpart_account']

        return values
