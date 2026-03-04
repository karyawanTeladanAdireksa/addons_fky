# -*- coding: utf-8 -*-
import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
#import openerp.addons.decimal_precision as dp

class account_register_payments(models.TransientModel):
    _inherit = "account.payment.register"
    
    def _get_register_invoices(self):
        return self.env['account.move'].browse(self._context.get('active_ids'))
    
    def _get_register_lines(self, register_ids):
        registers = []
        if register_ids:
            for register in register_ids:
                registers.append(register.id)
        return self.env['account.register.line'].browse(registers)
    
    payment_adm = fields.Selection([
            ('cash','Cash'),
            ('free_transfer','Non Payment Administration Transfer'),
            ('transfer','Transfer'),
            #('check','Check/Giro'),
            #('letter','Letter Credit'),
            ('cc','Credit Card'),
            ('dc','Debit Card'),
            ],string='Payment Adm')
    card_number = fields.Char('Card Number', size=128, required=False)
    card_type = fields.Selection([
            ('visa','Visa'),
            ('master','Master'),
            ('bca','BCA Card'),
            ('citi','CITI Card'),
            ('amex','AMEX'),
            ], string='Card Type', size=128)
    register_ids = fields.One2many('account.register.line', 'register_id', copy=False, string='Register Invoice')
    
    # @api.onchange('register_ids')
    # def _onchange_register_ids(self):
    #     amount = 0.0
    #     for line in self.register_ids:
    #         amount += line.amount_to_pay
    #     self.amount = amount
    #     return
    
    
#     @api.model
#     def default_get(self, fields):
#         rec = super(account_register_payments, self).default_get(fields)
#         active_ids = self._context.get('active_ids')
#         if not active_ids:
#             return rec
#         invoices = self.env['account.move'].browse(active_ids)
# 
#         # Check all invoices are open
#         if any(invoice.state != 'posted' or invoice.payment_state != 'not_paid' or not invoice.is_invoice() for invoice in invoices):
#             raise UserError(_("You can only register payments for open invoices"))
#         # Check all invoices are inbound or all invoices are outbound
#         outbound_list = [invoice.is_outbound() for invoice in invoices]
#         first_outbound = invoices[0].is_outbound()
#         if any(x != first_outbound for x in outbound_list):
#             raise UserError(_("You can only register at the same time for payment that are all inbound or all outbound"))
#         if any(inv.company_id != invoices[0].company_id for inv in invoices):
#             raise UserError(_("You can only register at the same time for payment that are all from the same company"))
#         # Check the destination account is the same
#         destination_account = invoices.line_ids.filtered(lambda line: line.account_internal_type in ('receivable', 'payable')).mapped('account_id')
#         if len(destination_account) > 1:
#             raise UserError(_('There is more than one receivable/payable account in the concerned invoices. You cannot group payments in that case.'))
#         if 'invoice_ids' not in rec:
#             rec['invoice_ids'] = [(6, 0, invoices.ids)]
#         if 'journal_id' not in rec:
#             rec['journal_id'] = self.env['account.journal'].search([('company_id', '=', self.env.company.id), ('type', 'in', ('bank', 'cash'))], limit=1).id
#         if 'payment_method_id' not in rec:
#             if invoices[0].is_inbound():
#                 domain = [('payment_type', '=', 'inbound')]
#             else:
#                 domain = [('payment_type', '=', 'outbound')]
#             rec['payment_method_id'] = self.env['account.payment.method'].search(domain, limit=1).id
#         return rec
    
    # @api.model
    # def default_get(self, fields):
    #     rec = super(account_register_payments, self).default_get(fields)
    #     context = dict(self._context or {})
    #     active_model = context.get('active_model')
    #     active_ids = context.get('active_ids')
         
    #     reg_lines = []
    #     communication = []
    #     for invoice in self.env[active_model].browse(active_ids):
    #         if invoice.invoice_origin:
    #             name = invoice.name +':'+ invoice.invoice_origin
    #         else:
    #             name = invoice.name
    #         communication.append(name)
    #         reg_lines.append([0, 0, {
    #            'invoice_id': invoice.id,
    #            'name':  name,
    #            'amount_total': invoice.amount_total,
    #            'residual': invoice.amount_residual,
    #            'amount_to_pay': invoice.amount_residual,
    #            }])
    #     rec.update({
    #         #HIDE
    #         'register_ids': reg_lines,
    #         'communication': ", ".join(communication),
    #     })
    #     #print ("===rec===",rec)
    #     return rec
    
#     @api.onchange('register_ids')
#     def _onchange_register_ids(self):
#         amount = 0.0
#         for line in self.register_ids:
#             amount += line.amount_to_pay
#         self.amount = amount
#         return    

    def get_payment_line_vals(self, payment, line):
        #print (""" Hook for extension """,line.residual,line.amount_total,line.amount_to_pay,self.amount)
        vals = {
            'to_reconcile': line.residual == line.amount_to_pay,
            'payment_id': payment.id,
            'name': line.name,
            'invoice_id': line.invoice_id.id,
            'date': line.invoice_id.invoice_date,
            'date_due': line.invoice_id.invoice_date_due or line.invoice_id.invoice_date,
            'move_line_id': line.invoice_id.line_ids.filtered(lambda x: x.account_id.internal_type in ('receivable', 'payable')).id,#(lambda x: x.account_id == line.invoice_id.account_id).id,
            'type': line.invoice_id.move_type in ['in_invoice', 'out_refund'] and 'cr' or 'dr',
            'amount_total': line.amount_total,
            'residual': line.residual,
            'amount_to_pay': line.amount_to_pay,
            'payment_difference': line.payment_difference,
            'payment_difference_handling': line.payment_difference_handling,
            'writeoff_account_id': line.writeoff_account_id and line.writeoff_account_id.id or False,
        }
        #print ('===vals==',vals)
        return vals
        
#     def _prepare_payment_vals(self, invoices):
#         '''Create the payment values.
#
#         :param invoices: The invoices that should have the same commercial partner and the same type.
#         :return: The payment values as a dictionary.
#         '''
#         res = super(account_register_payments, self)._prepare_payment_vals(invoices)
#         #amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)        
#         amount = 0.0
#         for line in self.register_ids:
#             amount += line.amount_to_pay
# #         print ('===res===',res,self)
# #         for line in self._get_register_lines(self.register_ids):
# #             self.env['account.payment.line'].create(self.get_payment_line_vals(self, line))
#         res['payment_adm'] = self.payment_adm
#         res['amount'] = abs(amount)
#         res['card_number'] = self.card_number
#         res['card_type'] = self.card_type
#         return res
    
    def _create_payment_vals_from_wizard(self):
        payment_vals = super(account_register_payments, self)._create_payment_vals_from_wizard()
        # payment_vals = {
        #     'date': self.payment_date,
        #     'amount': self.amount,
        #     'payment_type': self.payment_type,
        #     'partner_type': self.partner_type,
        #     'ref': self.communication,
        #     'journal_id': self.journal_id.id,
        #     'currency_id': self.currency_id.id,
        #     'partner_id': self.partner_id.id,
        #     'partner_bank_id': self.partner_bank_id.id,
        #     'payment_method_id': self.payment_method_id.id,
        #     'destination_account_id': self.line_ids[0].account_id.id
        # }
        #
        # if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
        #     payment_vals['write_off_line_vals'] = {
        #         'name': self.writeoff_label,
        #         'amount': self.payment_difference,
        #         'account_id': self.writeoff_account_id.id,
        #     }
        # amount = 0.0
        # for line in self.register_ids:
        #     amount += line.amount_to_pay
        #print ('--amount-',self.register_ids)
        payment_vals['payment_adm'] = self.payment_adm
        # payment_vals['amount'] = abs(amount) if self.register_ids else self.amount
        payment_vals['card_number'] = self.card_number
        payment_vals['card_type'] = self.card_type
        #payment_vals['register_ids'] = [(6, 0, self.register_ids.ids)]
        # register_ids = []
        # for line in self._get_register_lines(self.register_ids):
        #     #register_ids.append(self.get_payment_line_vals(self, line))
        #     self.env['account.payment.line'].create(self.get_payment_line_vals(self, line))
        #print ('===register_ids===',register_ids)
        #payment_vals['register_ids'] = self.env['account.payment.line'].create(reg for reg in register_ids)
        #payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
        #print ('===payment_vals===',payment_vals)
        return payment_vals

    # def _create_payments(self):
    #     payments = super(account_register_payments, self)._create_payments()
    #     for line in self._get_register_lines(self.register_ids):
    #         self.env['account.payment.line'].with_context(wizard_register=True).create(self.get_payment_line_vals(payments, line))
    #     return payments

    
    # def _create_payments(self):
    #     self.ensure_one()
    #     batches = self._get_batches()
    #     edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
    #     to_process = []
    #     print ('=_create_payments==',edit_mode)
    #     if edit_mode:
    #         payment_vals = self._create_payment_vals_from_wizard()
    #         to_process.append({
    #             'create_vals': payment_vals,
    #             'to_reconcile': batches[0]['lines'],
    #             'batch': batches[0],
    #         })
    #     else:
    #         # Don't group payments: Create one batch per move.
    #         if not self.group_payment:
    #             new_batches = []
    #             for batch_result in batches:
    #                 for line in batch_result['lines']:
    #                     new_batches.append({
    #                         **batch_result,
    #                         'payment_values': {
    #                             **batch_result['payment_values'],
    #                             'payment_type': 'inbound' if line.balance > 0 else 'outbound'
    #                         },
    #                         'lines': line,
    #                     })
    #             batches = new_batches

    #         for batch_result in batches:
    #             to_process.append({
    #                 'create_vals': self._create_payment_vals_from_batch(batch_result),
    #                 'to_reconcile': batch_result['lines'],
    #                 'batch': batch_result,
    #             })
    #     #for line in self._get_register_lines(self.register_ids):
    #     #    self.env['account.payment.line'].create(self.get_payment_line_vals(self, line))
    #     # to_process.append({
    #     #     'register_ids': [self.env['account.payment.line'].create(self.get_payment_line_vals(self, line)) for line in self._get_register_lines(self.register_ids)]
    #     # })

    #     payments = self._init_payments(to_process, edit_mode=edit_mode)
    #     self._post_payments(to_process, edit_mode=edit_mode)
    #     self._reconcile_payments(to_process, edit_mode=edit_mode)
    #     x
    #     return payments

    # def _create_payments(self):
    #     payments = super(account_register_payments, self)._create_payments()
    #     #print ('===_create_payments===',payments)
    #     for line in self._get_register_lines(self.register_ids):
    #         self.env['account.payment.line'].create(self.get_payment_line_vals(payments, line))
    #     return payments 
    
#     def create_payments(self):
#         print ('''Create payments according to the invoices.
#         Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
#         leads to multiple payments.
#         In case of all the invoices are related to the same commercial_partner_id and have the same type,
#         only one payment will be created.
# 
#         :return: The ir.actions.act_window to show created payments.
#         ''')
#         Payment = self.env['account.payment']
#         payments = Payment.create(self.get_payments_vals())
# #         payments = Payment
# #         for payment_vals in self.get_payments_vals():
# #             payments += Payment.create(payment_vals)
#         #===================================================================
#         # ADD PAYMENT LINE
#         #===================================================================
#         for payment in payments:
#             for line in self._get_register_lines(self.register_ids):
#                 self.env['account.payment.line'].create(self.get_payment_line_vals(payment, line))
#         #===================================================================
#         #payments.post()
#         return {
#             'name': _('Payments'),
#             'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
#             'view_type': 'form',
#             'view_mode': 'tree,form',
#             'res_model': 'account.payment',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#         }
        
#     def _prepare_communication(self, invoices):
#         '''Define the value for communication field
#         Append all invoice's references together.
#         '''
#         return " ".join(i.invoice_payment_ref or i.ref or i.name for i in invoices)

#     def _prepare_payment_vals(self, invoices):
#         '''Create the payment values.
# 
#         :param invoices: The invoices/bills to pay. In case of multiple
#             documents, they need to be grouped by partner, bank, journal and
#             currency.
#         :return: The payment values as a dictionary.
#         '''
#         amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
#         values = {
#             'journal_id': self.journal_id.id,
#             'payment_method_id': self.payment_method_id.id,
#             'payment_date': self.payment_date,
#             'communication': self._prepare_communication(invoices),
#             'invoice_ids': [(6, 0, invoices.ids)],
#             'payment_type': ('inbound' if amount > 0 else 'outbound'),
#             'amount': abs(amount),
#             'currency_id': invoices[0].currency_id.id,
#             'partner_id': invoices[0].commercial_partner_id.id,
#             'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
#             'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
#         }
#         return values

#     def _get_payment_group_key(self, invoice):
#         """ Returns the grouping key to use for the given invoice when group_payment
#         option has been ticked in the wizard.
#         """
#         return (invoice.commercial_partner_id, invoice.currency_id, invoice.invoice_partner_bank_id, MAP_INVOICE_TYPE_PARTNER_TYPE[invoice.type])

#     def get_payments_vals(self):
#         '''Compute the values for payments.
#
#         :return: a list of payment values (dictionary).
#         '''
#         grouped = defaultdict(lambda: self.env["account.move"])
#         for inv in self.invoice_ids:
#             if self.group_payment:
#                 grouped[self._get_payment_group_key(inv)] += inv
#             else:
#                 grouped[inv.id] += inv
#         return [self._prepare_payment_vals(invoices) for invoices in grouped.values()]
#
#     def create_payments(self):
#         '''Create payments according to the invoices.
#         Having invoices with different commercial_partner_id or different type
#         (Vendor bills with customer invoices) leads to multiple payments.
#         In case of all the invoices are related to the same
#         commercial_partner_id and have the same type, only one payment will be
#         created.
#
#         :return: The ir.actions.act_window to show created payments.
#         '''
#         context = dict(self._context or {})
#         Payment = self.env['account.payment']
#         payments = Payment.create(self.get_payments_vals())
#
# #         for payment_vals in self.get_payments_vals():
# #             payments += Payment.create(payment_vals)
#         #===================================================================
#         # ADD PAYMENT LINE
#         #===================================================================
#         for payment in payments:
#             for line in self._get_register_lines(self.register_ids):
#                 self.env['account.payment.line'].create(self.get_payment_line_vals(payment, line))
#         #===================================================================
#         if not context.get('to_pay'):
#             payments.post()
#
#         action_vals = {
#             'name': _('Payments'),
#             'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
#             'res_model': 'account.payment',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#         }
#         if len(payments) == 1:
#             action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
#         else:
#             action_vals['view_mode'] = 'tree,form'
#         return action_vals
    
#     #@api.multi
#     def create_payment(self):
#         payment = self.env['account.payment'].create(self.get_payment_vals())
#         if payment:
#             for line in self._get_register_lines(self.register_ids):
#                 self.env['account.payment.line'].create(self.get_payment_line_vals(payment, line))
#             payment.write({'register_date': self.payment_date, 
#                            'is_force_curr': self.is_force_curr, 
#                            'force_rate': self.force_rate,
#                            'payment_adm': self.payment_adm,
#                            'card_number': self.card_number,
#                            'card_type': self.card_type,
#                            })
#         payment.post_multi()
#         return payment#{'type': 'ir.actions.act_window_close'}
    
#     #@api.multi
#     def get_payments_vals(self):
#         '''Compute the values for payments.
# 
#         :return: a list of payment values (dictionary).
#         '''
#         if self.multi:
#             groups = self._groupby_invoices()
#             return [self._prepare_payment_vals(invoices) for invoices in groups.values()]
#         return [self._prepare_payment_vals(self.invoice_ids)]
#     
#     #@api.multi
#     def create_payments(self):
#         '''Create payments according to the invoices.
#         Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
#         leads to multiple payments.
#         In case of all the invoices are related to the same commercial_partner_id and have the same type,
#         only one payment will be created.
# 
#         :return: The ir.actions.act_window to show created payments.
#         '''
#         Payment = self.env['account.payment']
#         payments = Payment
#         for payment_vals in self.get_payments_vals():
#             payments += Payment.create(payment_vals)
#         payments.post()
# 
#         action_vals = {
#             'name': _('Payments'),
#             'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
#             'view_type': 'form',
#             'res_model': 'account.payment',
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#         }
#         if len(payments) == 1:
#             action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
#         else:
#             action_vals['view_mode'] = 'tree,form'
#         return action_vals
    
class account_register_line(models.TransientModel):
    _name = 'account.register.line'
    _description = 'Account Line Register'

#     def _compute_total_invoices_amount(self):
#         """ Compute the sum of the residual of invoices, expressed in the payment currency """
#         payment_currency = self.currency_id or self.register_id.journal_id.currency_id or self.register_id.journal_id.company_id.currency_id or self.env.user.company_id.currency_id
#         if self.invoice_id.company_currency_id != payment_currency:
#             total = self.invoice_id.company_currency_id.with_context(date=self.register_id.payment_date).compute(self.invoice_id.residual_company_signed, payment_currency)
#         else:
#             total = self.invoice_id.residual_company_signed
#         return abs(total)
#     
#     @api.one
#     @api.depends('invoice_id', 'amount_to_pay', 'register_id.payment_date', 'currency_id')
#     def _compute_payment_difference(self):
#         if self.invoice_id.type in ['in_invoice', 'out_refund']:
#             self.payment_difference = self.amount_to_pay - self._compute_total_invoices_amount()
#         else:
#             self.payment_difference = self._compute_total_invoices_amount() - self.amount_to_pay
        
    @api.depends('invoice_id', 'amount_total', 'residual', 'amount_to_pay', 'register_id.payment_date','currency_id')
    def _compute_payment_difference(self):
        #self.ensure_one()
        #self.payment_difference = self.residual - self.amount_to_pay
        #draft_payments = self.filtered(lambda p: p.invoice_ids and p.state == 'draft')
        for pay in self:
            pay.payment_difference = pay.residual - pay.amount_to_pay
            #payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
            #pay.payment_difference = pay._compute_payment_amount(pay.invoice_ids, pay.currency_id, pay.journal_id, pay.payment_date) - payment_amount
        #(self - draft_payments).payment_difference = 0
        
    
#     @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'payment_type')
#     def _compute_payment_difference(self):
#         draft_payments = self.filtered(lambda p: p.invoice_ids and p.state == 'draft')
#         for pay in draft_payments:
#             payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
#             pay.payment_difference = pay._compute_payment_amount(pay.invoice_ids, pay.currency_id, pay.journal_id, pay.payment_date) - payment_amount
#         (self - draft_payments).payment_difference = 0
        
    register_id = fields.Many2one('account.payment.register', string='Register Payment')
    name = fields.Char(string='Description', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    currency_invoice_id = fields.Many2one('res.currency', related='invoice_id.currency_id', string='Currency')
    amount_total = fields.Monetary('Amount Invoice', required=True, digits='Account')
    residual = fields.Monetary('Balance Invoice', required=True, digits='Account')
    currency_id = fields.Many2one('res.currency',  string='Currency')  
    to_reconcile = fields.Boolean('To Pay')
    amount_to_pay = fields.Monetary('Allocation', required=True, digits='Account')
    action = fields.Boolean('Action')
    payment_difference = fields.Monetary(compute='_compute_payment_difference', string='Payment Difference', readonly=True)
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')], default='open', string="Write-off", copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Write-off Account", domain=[('deprecated', '=', False)], copy=False)
    
    @api.onchange('action')
    def _onchange_action(self):
        if not self.action:
            return
        self.amount_to_pay = self.action and self.residual or 0.0
    