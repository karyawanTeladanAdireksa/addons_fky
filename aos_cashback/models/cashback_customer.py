# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta



# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MasterCustomerCashback(models.Model):

    _name = "master.customer.cashback"
    _description = "Master Customer Cashback"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "group_id"

    name = fields.Char(string='Number', required=True, copy=False,
                       readonly=True, index=True, default=lambda self: _('New'))
    cashback_name = fields.Char(string='Cashback Name')
    date = fields.Date()
    active = fields.Boolean(default=True)
    cashback_type = fields.Selection([('group', 'Customer Group'), (
        'customer', 'Customer')], default='group', string='Cashback Type')
    partner_id = fields.Many2one('res.partner', string='Customer')
    group_id = fields.Many2one('adireksa.customer.target', string='Customer Group')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Running'), ('cancel', 'Cancel')],
                             default='draft', string='Status', readonly=True, copy=False, index=True)
    # account_id = fields.Many2one('account.account', string='Cashback Account')
    # expense_account_id = fields.Many2one(
    #     'account.account', string='Cashback Expense Account')
    cashback_in = fields.Float('Cashback In', compute='compute_cashback_in' ,copy=False)
    cashback_used = fields.Float('Cashback Out', compute='compute_cashback_used' , copy=False)
    balance = fields.Float('Balance', compute='compute_cashback_balance')
    # journal_id = fields.Many2one('account.journal', 'Journal')
    line_ids = fields.One2many(
        'cashback.lines', 'cashback_id', 'Cashback Summary')
    manual_line_ids = fields.One2many(
        'manual.cashback.lines', 'cashback_id', 'Manual Cashback')
    cashback_internal_category_ids = fields.One2many(
        'cashback.internal.category.lines', 'cashback_id', 'Manual Cashback')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    cashback_pending = fields.Float(
        'Cashback Pending', compute="compute_cashback_pending")
    # cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), (
    #     'customer_invoice', 'Customer Invoice')], related="company_id.cashback_deduction_option", string="Cashback Deduction Option")
    automatic_line_ids = fields.One2many('automatic.cashback.lines', 'cashback_id', string='Automatic Cashback')
    cashback_used_id = fields.One2many('cashback.used.lines', 'cashback_id', string='Cashback Used')
    cashback_product_ids = fields.One2many('cashback.product.lines', 'cashback_id', string='Cashback Product')
    group_class_id = fields.Many2one('cashback.class.group',string="Group Class",related='group_id.group_class_id')
    
    @api.depends('line_ids')
    def compute_cashback_in(self):
        for rec in self:
            rec.cashback_in = sum(rec.line_ids.filtered(lambda x:x.default_posting == 'debit' and x.state == 'approve').mapped('value'))
    
    @api.depends('line_ids')
    def compute_cashback_used(self):
        for rec in self:
            rec.cashback_used = sum(rec.line_ids.filtered(lambda x:x.default_posting == 'credit' and x.state == 'approve' ).mapped('value'))

    @api.depends('cashback_in', 'cashback_used', 'cashback_pending')
    def compute_cashback_balance(self):
        for rec in self:
            rec.balance = rec.cashback_in - rec.cashback_used

    @api.depends('line_ids.value', 'line_ids.state')
    def compute_cashback_pending(self):
        for rec in self:
            rec.cashback_pending = sum(
                [line.value for line in rec.line_ids.filtered(lambda x: x.state == 'pending')])

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'master.customer.cashback') or _('New')
        return super(MasterCustomerCashback, self).create(vals)
    
    def unlink(self):
        for rec in self:
            if rec.state == 'approve':
                raise UserError(_('Master Cashback Dalam Status Running, Tidak Bisa Di Delete'))
        return super(MasterCustomerCashback, self).unlink()

    def action_confirm(self):
        self.write({'state': 'confirm'})
        return True
    
    def action_draft(self):
        self.write({'state': 'draft'})
        return True
    
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True


class CashbackLines(models.Model):

    _name = 'cashback.lines'
    _description = 'Cashback Lines'
    _order = 'create_date DESC'
    
    name = fields.Char('Transaction Number')
    partner_id = fields.Many2one('res.partner', 'Customer')
    group_id = fields.Many2one('adireksa.customer.target',string="Customer Group")
    account_id = fields.Many2one('account.move',string="Invoice ID")
    date = fields.Date('Transaction Date')
    days = fields.Char('Days')
    communication = fields.Char()
    # type_id = fields.Many2one('cashback.type', 'Type')
    # default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    cashback_rule = fields.Char(string="Cashback Rule")
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    value = fields.Float()
    reference = fields.Char()
    payment_name = fields.Char()
    cashback_id = fields.Many2one('master.customer.cashback')
    state = fields.Selection([('pending', 'Cancelled'), ('approve', 'Approved')],
                             default='pending', string='Status', readonly=True, copy=False, index=True)
    

    # def _action_approve_cashback(self):
    #     self = self.env['cashback.lines'].search([])
    #     for rec in self:
    #         if rec.id not in [993, 994, 992, 982, 978, 980, 979, 977, 981, 953, 952, 945, 946, 947, 948, 949, 950, 951, 944, 943, 942, 941, 940, 939, 938, 937, 936, 935, 934, 933, 932, 925, 922, 924, 927, 926, 923, 903, 906, 905, 904, 901, 902, 875, 823, 653, 691, 680, 681, 682, 688, 689, 654, 655, 656, 652, 651, 650, 649, 648, 657, 658, 659, 660, 661, 662, 671, 672, 673, 674, 675, 676, 677, 678, 679, 663, 664, 665, 666, 690, 683, 684, 685, 686, 687, 667, 668, 669, 670, 631, 469, 470, 448, 446, 447, 443, 445, 444, 408, 383, 382, 381, 380, 379, 378, 369, 362, 364, 361, 363, 358, 360, 356, 357, 359, 214, 208, 209, 207, 198, 199, 200, 201, 202, 203, 204, 171, 164, 166, 165, 159, 160, 161, 156, 157, 158, 139, 140, 141, 142, 144, 143, 153, 154, 155, 151, 152, 138, 150, 137, 136, 135, 149, 148, 147, 146, 145, 132, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 133, 134, 118, 117, 116, 115] :
    #             rec.state = 'approve'
    #         print('xx')

    def write(self,vals):
        res = super(CashbackLines,self).write(vals)
        if vals and self:
            msg = _(f'{self.env.user.name}+{vals}')
            self.cashback_id.message_post(body=msg)
        return res
    
    
class InternalCashback(models.Model):

    _name = 'cashback.product.lines'
    _description = 'Manual Cashback Product Lines'
    _order = 'create_date DESC'

    date = fields.Date('Date')
    name = fields.Char(string='Name')
    # type_id = fields.Many2one('cashback.type', 'Type')
    # default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('cancel', 'Cancelled'),(
        'approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    cashback_id = fields.Many2one('master.customer.cashback')
    # line_ids = fields.One2many(
    #     'manual.cashback.so.lines', 'manual_cashback_id')

    value = fields.Float('Value')

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True


class InternalCashback(models.Model):

    _name = 'cashback.internal.category.lines'
    _description = 'Manual Cashback Lines'
    _order = 'create_date DESC'

    date = fields.Date('Date')
    name = fields.Char(string='Name')
    # type_id = fields.Many2one('cashback.type', 'Type')
    # default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('cancel', 'Cancelled'),(
        'approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    cashback_id = fields.Many2one('master.customer.cashback')
    # line_ids = fields.One2many(
    #     'manual.cashback.so.lines', 'manual_cashback_id')

    value = fields.Float('Value')

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True


class ManualCashbackLines(models.Model):

    _name = 'manual.cashback.lines'
    _description = 'Manual Cashback Lines'
    _order = 'create_date DESC'

    date = fields.Date('Date')
    name = fields.Char(string='Name')
    # type_id = fields.Many2one('cashback.type', 'Type')
    # default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('cancel', 'Cancelled'),(
        'approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback')
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    # line_ids = fields.One2many(
    #     'manual.cashback.so.lines', 'manual_cashback_id')

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    real_omset = fields.Float('Real Omset')
    total_omset = fields.Float('Total Omset')
    final_omset = fields.Float('Final Omset')
    cashback = fields.Float('Cashback %')
    value = fields.Float('Value')
    cashback_calculation = fields.Boolean('Cashback Calculation')

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True

#
# class ManualCashbackSoLines(models.TransientModel):
#
#     _name = 'manual.cashback.so.lines'
#     _description = 'Manual Cashback SO Lines'
#
#     so_id = fields.Many2one('sale.order', 'SO Number')
#     so_date = fields.Date('SO Date')
#     so_value = fields.Float('SO Value')
#     manual_cashback_id = fields.Many2one('manual.cashback.lines')

# class MasterCustomerCashback(models.Model):
#     _inherit = 'master.customer.cashback'
#
#     cashback_type = fields.Selection([('group', 'Customer Group'), ('customer', 'Customer')],
#         default='group', string='Cashback Type')
    # automatic_line_ids = fields.One2many('automatic.cashback.lines', 'cashback_id', string='Automatic Cashback')
    # paid_line_ids = fields.One2many('payment.cashback.lines', 'cashback_id', string='Cashback Rule')

    # def compute_cashback_used(self):
    #     res = super(MasterCustomerCashback, self).compute_cashback_used()
    #     for rec in self:
    #         rec.cashback_used += sum([line.value for line in rec.automatic_line_ids.filtered(
    #             lambda x: x.type_id.default_posting == 'credit' and x.state == 'approve')])
    #         rec.cashback_used += sum([line.value for line in rec.paid_line_ids.filtered(
    #             lambda x: x.type_id.default_posting == 'credit' and x.state == 'approve')])
    #     return res
    #
    # def compute_cashback_in(self):
    #     res = super(MasterCustomerCashback, self).compute_cashback_in()
    #     for rec in self:
    #         rec.cashback_in += sum([line.value for line in rec.automatic_line_ids.filtered(
    #             lambda x: x.type_id.default_posting == 'debit' and x.state == 'approve')])
    #         rec.cashback_in += sum([line.value for line in rec.paid_line_ids.filtered(
    #             lambda x: x.type_id.default_posting == 'debit' and x.state == 'approve')])
    #     return res

    # def print_cashback_report(self):
    #     view = self.env.ref('adireksa_cashback_pattern.cashback_print_view')
    #     return {
    #         'name': _('Print Cashback Report'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'cashback.print',
    #         'views': [(view.id, 'form')],
    #         'view_id': view.id,
    #         'target': 'new',
    #     }

#
# class MasterCashbackProduct(models.Model):
#     _inherit = 'master.cashback.product'
#
#     cashback_type = fields.Selection([('group', 'Customer Group'), ('customer', 'Customer')],
#         default='group', string='Cashback Type')


class AutomaticCashbackLines(models.Model):
    _name = 'automatic.cashback.lines'
    _description = 'Automatic Cashback Lines'
    _order = 'create_date DESC'

    name = fields.Char(string='Name')
    date = fields.Date('Date')
    # type_id = fields.Many2one('cashback.type', 'Type')
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('cancel', 'Cancelled'),(
        'approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    cashback_rule = fields.Char(string="Cashback Rule")
    communication = fields.Char()
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback')
    value = fields.Float('Value')
    payment_name = fields.Char()
    cashback_rule_id = fields.Many2many('cashback.rule.line', 'automatic_cashback_rule_rel', string='Cashback Rule')

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True

class CashbackUsedLines(models.Model):
    _name = 'cashback.used.lines'
    _description = 'Cashback Used Lines'
    _order = 'create_date DESC'

    name = fields.Char(string='Name')
    date = fields.Date('Date')
    # type_id = fields.Many2one('cashback.type', 'Type')
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    reference = fields.Char('Reference')
    account_id = fields.Many2one('account.move',string="Invoice ID")
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('cancel', 'Cancelled'),(
        'approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback')
    value = fields.Float('Value')


    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True


class PaymentCashbackLines(models.Model):
    _name = 'payment.cashback.lines'
    _description = 'Payment Cashback Lines'
    _order = 'create_date DESC'

    date = fields.Date('Date')
    name = fields.Char(string='Name')
    # type_id = fields.Many2one('cashback.type', 'Type')
    # default_posting = fields.Selection(related='type_id.default_posting', string='Default Posting')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('cancel', 'Cancelled'),(
        'approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one(
        'res.users', string='Add By', default=lambda self: self.env.user)
    default_posting = fields.Selection([('debit', 'Debit'), ('credit', 'Credit')], 'D/C', default="debit", tracking=True)
    # cashback_id = fields.Many2one('master.customer.cashback')
    value = fields.Float('Value')
    payment_id = fields.Many2one('account.payment', string='Payment Receipt')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    # cashback_rule_id = fields.Many2one('cashback.rule.line', string='Cashback Rule')
    # amount_total = fields.Float(string='Nilai Nota', compute='_compute_total', default=0.0)
    # total_day = fields.Integer(string='Days', compute='_compute_total', default=0)

    # def _compute_total(self):
    #     cr = self.env.cr
    #     for rec in self:
    #         cr.execute("""SELECT apr.amount as amount, paml.date
    #             FROM account_partial_reconcile apr
    #             INNER JOIN account_move_line paml ON paml.id = apr.credit_move_id
    #             INNER JOIN account_move_line iaml ON iaml.id = apr.debit_move_id
    #             WHERE iaml.move_id = {0} and paml.payment_id = {1}""".format(rec.invoice_id.id, rec.payment_id.id))
    #         res = cr.dictfetchone()
    #         payment_amount = res['amount'] if res['amount'] else 0.0
    #         pdate = res['date'] if res['date'] else False
    #         if pdate:
    #             payment_date = datetime.strptime(str(pdate), '%Y-%m-%d')
    #             curr_date = datetime.strptime(str(rec.invoice_id.invoice_date), '%Y-%m-%d')
    #             date_diff = abs((payment_date - curr_date).days)
    #         else:
    #             date_diff = 0
    #         rec.amount_total = payment_amount
    #         rec.total_day = date_diff

    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    def action_waiting_for_approval(self):
        self.write({'state': 'waiting_for_approval'})
        return True
