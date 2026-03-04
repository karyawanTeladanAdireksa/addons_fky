# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), ('customer_invoice', 'Customer Invoice')], related="company_id.cashback_deduction_option", string="Cashback Deduction Option")
    cashback_value = fields.Float('Cashback Value')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('cashback_per', 'amount_total', 'cashback')
    def compute_cashback_value(self):
        for rec in self:
            if rec.cashback:
                rec.cashback_value = ((rec.amount_total * rec.cashback_per)/100.0)
                if rec.cashback_value > rec.max_cashback:
                    rec.cashback_value = rec.max_cashback
    
    @api.depends('cashback')
    def compute_max_cashback(self):
        for record in self:
            if len(record.invoice_ids) == 0:
                return
            if record.invoice_ids[0]:
                Values = self.env['ir.values'].sudo() or self.env['ir.values']
                max_cashback = Values.get_default('account.config.settings', 'max_cashback') or 0.0
                if record.amount and max_cashback:
                    record.max_cashback = ((record.invoice_ids[0].amount_total * max_cashback)/100.0) - record.invoice_ids[0].cashback_value

    @api.onchange('cashback_value', 'cashback')
    def onchange_cashback(self):
        for rec in self:
            if not rec.cashback:
                rec.cashback_value = 0.0
            else:
                if rec.cashback_value > rec.max_cashback:
                    raise UserError(_("Cashback Value can't be bigger than Max Cashback!"))

    # @api.depends('invoice_ids', 'amount', 'date', 'currency_id', 'cashback_value')
    # def _compute_payment_difference(self):
    #     res = super(AccountPayment, self)._compute_payment_difference()
    #     for rec in self:
    #         rec.payment_difference = rec.payment_difference - rec.cashback_value
    #     return res

    cashback_value = fields.Float('Cashback Value', compute='compute_cashback_value')
    cashback = fields.Boolean(string='Cashback')
    amount_total = fields.Float('Amount Total')
    max_cashback = fields.Float(string='Max Cashback', compute='compute_max_cashback')
    get_cashback = fields.Boolean(related='partner_id.get_cashback', store=True)
    edit_cashback = fields.Boolean(related='partner_id.edit_cashback', store=True)
    cashback_per = fields.Float('Cashback %')
    cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), ('customer_invoice', 'Customer Invoice')], string="Cashback Deduction Option", default=lambda
         self: self.env.user.company_id.cashback_deduction_option)
    invoice_age = fields.Integer('Invoice Ages', compute="compute_invoice_age")

    @api.depends('date')
    def compute_invoice_age(self):
        for res in self:
            if 'invoice_date' in self._context or res.date:
                invoice_date = datetime.strptime(str(self._context.get('invoice_date')) or str(res.date), '%Y-%m-%d').date()
                res.invoice_age = ((date.today() - invoice_date).days) + 1

    # 
    # def post(self):
        # res = super(AccountPayment, self).post()
        # ml_obj = self.env['account.move.line']
        # for move in self:
            # if move.cashback and move.cashback_value > 0:
                # invoice = move.invoice_ids and move.invoice_ids[0] or False
                # if move.get_cashback and invoice:
                    # domain = []
                    # if move.partner_id.category_id:
                        # domain += [('group_id', 'in', move.partner_id.category_id.ids)]
                    # else:
                        # domain += [('partner_id', '=', move.partner_id.id)]
                    # mcc_rec = self.env['master.customer.cashback'].search(domain, limit=1)
                    # type = self.env['cashback.type'].search([('name', '=', 'Customer Invoice')])
                    # if mcc_rec:
                        # self.env['cashback.lines'].create({'name': invoice.number,
                                      # 'partner_id' : invoice.partner_id.id,
                                      # 'date': invoice.date_invoice, 
                                      # 'type_id': type.id,
                                      # 'value': move.cashback_value,
                                      # 'reference': invoice.name,
                                      # 'cashback_id': mcc_rec.id})
                        # if mcc_rec.line_ids.mapped('name') == invoice.origin:
                            # jkjkjkjkj
                        # print ("======", mcc_rec.line_ids.mapped('name'))
                        # jkjjj
                        # mcc_rec.cashback_used += move.cashback_value
                        # invoice.cashback_value += move.cashback_value
                        # move_id = move.move_line_ids.mapped('move_id')
                        # debit_line = move.move_line_ids.filtered(lambda self: self.debit > 0)
                        # debit_line.with_context(cashback=True).write({'debit': debit_line.debit - move.cashback_value})
                        # ml_obj.with_context(cashback=True).create({
                            # 'name': 'Cashback Value',
                            # 'move_id': move_id.id,
                            # 'journal_id': move.journal_id.id,
                            # 'date': datetime.now(),
                            # 'account_id': mcc_rec.account_id.id,
                            # 'debit': move.cashback_value,
                            # 'company_id': move.company_id.id
                        # })
        # return res

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for move in self:
            invoice = move.reconciled_invoice_ids and move.reconciled_invoice_ids[0] or False
            if invoice:
                domain = []
                if move.partner_id.category_id:
                    domain += [('group_id', 'in', move.partner_id.category_id.ids)]
                else:
                    domain += [('partner_id', '=', move.partner_id.id)]
                mcc_rec = self.env['master.customer.cashback'].search(domain, limit=1)
                if mcc_rec:
                    line = self.env['cashback.lines'].search([('cashback_id', '=', mcc_rec.id), ('name', '=', invoice.name)])
                    if line:
                        line.write({'state': 'approve'})
        return res


# class AccountMove(models.Model):

#     _inherit = 'account.move'

#     def assert_balanced(self):
#         if self.env.context.get('cashback'):
#             return True
#         return super(AccountMove, self).assert_balanced()


# class AccountMoveLine(models.Model):

#     _inherit = 'account.move.line'

#     
#     def _update_check(self):
#         """ Raise Warning to cause rollback if the move is posted, some entries are reconciled or the move is older than the lock date"""
#         move_ids = set()
#         for line in self:
#             if not self.env.context.get('cashback'):
#                 err_msg = _('Move name (id): %s (%s)') % (line.move_id.name, str(line.move_id.id))
#                 if line.move_id.state != 'draft':
#                     raise UserError(_('You cannot do this modification on a posted journal entry, you can just change some non legal fields. You must revert the journal entry to cancel it.\n%s.') % err_msg)
#                 if line.reconciled and not (line.debit == 0 and line.credit == 0):
#                     raise UserError(_('You cannot do this modification on a reconciled entry. You can just change some non legal fields or you must unreconcile first.\n%s.') % err_msg)
#                 if line.move_id.id not in move_ids:
#                     move_ids.add(line.move_id.id)
#         self.env['account.move'].browse(list(move_ids))._check_lock_date()
#         return True
    