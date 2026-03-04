# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
#import openerp.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


# class AccountTax(models.Model):
#     _inherit = 'account.tax'
     
#     is_expenses = fields.Boolean('Is Expenses', default=False)

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    tax_line_ids = fields.One2many('account.payment.tax', 'payment_id', string='Tax Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    def compute_taxes(self):
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        account_payment_tax = self.env['account.payment.tax']
        ctx = dict(self._context)
        for invoice in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM account_payment_tax WHERE move_id=%s AND manual is False", (invoice.id,))
            if self._cr.rowcount:
                self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = invoice.get_taxes_values()

            # Create new tax lines
            for tax in tax_grouped.values():
                account_payment_tax.create(tax)

        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'register_ids': []})
    
    
    @api.model
    def _get_tax_grouping_key_from_tax_line(self, line, tax_line):
        ''' Create the dictionary based on a tax line that will be used as key to group taxes together.
        /!\ Must be consistent with '_get_tax_grouping_key_from_base_line'.
        :param tax_line:    An account.move.line being a tax line (with 'tax_repartition_line_id' set then).
        :return:            A dictionary containing all fields on which the tax will be grouped.
        '''
        #print ('===_get_tax_grouping_key_from_tax_line==',tax_line)
        return {
            'payment_id': self.id,
            'id': tax_line['id'],
            'account_id': tax_line['account_id'],
            'name': tax_line['name'],
            'amount': tax_line['amount'],
            'base': tax_line['base'],
            'manual': False,
            'sequence': tax_line['sequence'],
            #'tax_repartition_line_id': tax_line['tax_repartition_line_id'],
            #'currency_id': tax_line['currency_id'],
            #'analytic_tag_ids': [(6, 0, tax_line.tax_line_id.analytic and tax_line.analytic_tag_ids.ids or [])],
            #'analytic_account_id': tax_line['analytic'] and line.account_analytic_id.id or False,
            #'tax_ids': tax_line['analytic'] and [(6, 0, tax_line['tax_ids'])],
            #'tag_ids': [(6, 0, tax_line['tag_ids'])],
        }
    
    # def _serialize_tax_grouping_key(self, grouping_dict):
    #     ''' Serialize the dictionary values to be used in the taxes_map.
    #     :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
    #     :return: A string representing the values.
    #     '''
    #     return '-'.join(str(v) for v in grouping_dict.values())
    
    # def _prepare_tax_line_vals(self, line, tax):
    #     """ Prepare values to create an account.invoice.tax line
    #
    #     The line parameter is an account.invoice.line, and the
    #     tax parameter is the output of account.tax.compute_all().
    #     """
    #     vals = {
    #         'payment_id': self.id,
    #         'name': tax['name'],
    #         'tax_id': tax['id'],
    #         'amount': tax['amount'],
    #         'base': tax['base'],
    #         'manual': False,
    #         'sequence': tax['sequence'],
    #         'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
    #         'account_id': self.payment_type in ('inbound') and (tax['account_id'] or line.move_id.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
    #         'analytic_tag_ids': tax['analytic'] and line.analytic_tag_ids.ids or False,
    #     }

        # If the taxes generate moves on the same financial account as the invoice line,
        # propagate the analytic account from the invoice line to the tax line.
        # This is necessary in situations were (part of) the taxes cannot be reclaimed,
        # to ensure the tax move is allocated to the proper analytic account.
#         if not vals.get('account_analytic_id') and line.account_analytic_id and vals['account_id'] == line.account_id.id:
#             vals['account_analytic_id'] = line.account_analytic_id.id
        # return vals

    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.register_ids:
            #if not line.account_id or line.display_type:
            #    continue
            if line.amount_to_pay:
                #print ("DOOR")
                price_unit = line.invoice_id.amount_untaxed if line.residual == line.amount_to_pay else line.amount_to_pay
                taxes = line.payment_line_wth_tax_ids.compute_all(price_unit, self.currency_id, 1.0, False, self.partner_id)['taxes']
                for tax in taxes:
                    #print ('=tax=',tax['id'])
                    grouping_dict = self._get_tax_grouping_key_from_tax_line(line, tax)
                    #grouping_key = self._serialize_tax_grouping_key(grouping_dict)
                    #print ('===grouping_key==',grouping_key)
                    #val = self._prepare_tax_line_vals(line, tax)
                    #key = self.env['account.tax'].browse(tax['id']).tax_group_id
                    key = line
                    #print ('===grouping_dict==',grouping_dict,key)
                    #tax_grouped[grouping_key]['amount'] += grouping_dict['amount']
                    #tax_grouped[grouping_key]['base'] = grouping_dict['base']
                    if key not in tax_grouped:
                        tax_grouped[key] = grouping_dict
                        tax_grouped[key]['base'] = round_curr(grouping_dict['base'])
                    else:
                        tax_grouped[key]['amount'] += grouping_dict['amount']
                        tax_grouped[key]['base'] += round_curr(grouping_dict['base'])
        return tax_grouped
    
    # def _get_computed_taxes(self):
    #     self.ensure_one()
    # #
    # #     if self.move_id.is_sale_document(include_receipts=True):
    # #         # Out invoice.
    # #         if self.product_id.taxes_id:
    # #             tax_ids = self.product_id.taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
    # #         elif self.account_id.tax_ids:
    # #             tax_ids = self.account_id.tax_ids
    # #         else:
    # #             tax_ids = self.env['account.tax']
    # #         if not tax_ids and not self.exclude_from_invoice_tab:
    # #             tax_ids = self.move_id.company_id.account_sale_tax_id
    # #     elif self.move_id.is_purchase_document(include_receipts=True):
    # #         # In invoice.
    # #         if self.product_id.supplier_taxes_id:
    # #             tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
    # #         elif self.account_id.tax_ids:
    # #             tax_ids = self.account_id.tax_ids
    # #         else:
    # #             tax_ids = self.env['account.tax']
    # #         if not tax_ids and not self.exclude_from_invoice_tab:
    # #             tax_ids = self.move_id.company_id.account_purchase_tax_id
    # #     else:
    # #         # Miscellaneous operation.
    # #         tax_ids = self.account_id.tax_ids
    # #
    #     if self.company_id and tax_ids:
    #         tax_ids = tax_ids.filtered(lambda tax: tax.company_id == self.company_id)
    #
    #     return tax_ids
    
    @api.onchange('register_ids', 'tax_line_ids', 'amount_charges')
    def _onchange_register_ids(self):
        amount = 0.0
        amount_charges = self.amount_charges
        others_grouped = []
        for line in self.register_ids:
            if line.amount_to_pay:
                others_grouped += [oth_line._prepare_other_line(line) for oth_line in line.invoice_id.other_line_ids]
            amount += line.amount_to_pay
        # taxes = self._get_computed_taxes()
        # if taxes and self.move_id.fiscal_position_id:
        #     price_subtotal = self._get_price_total_and_subtotal(price_unit=price_unit, taxes=taxes)['price_subtotal']
        #     accounting_vals = self._get_fields_onchange_subtotal(price_subtotal=price_subtotal, currency=self.move_id.company_currency_id)
        #     balance = accounting_vals['debit'] - accounting_vals['credit']
        #     price_unit = self._get_fields_onchange_balance(balance=balance).get('price_unit', price_unit)
        #
        # # Convert the unit price to the invoice's currency.
        # company = self.move_id.company_id
        # self.price_unit = company.currency_id._convert(price_unit, self.move_id.currency_id, company, self.move_id.date)
        taxes_grouped = self.get_taxes_values()
        #print ('===taxes_grouped==',others_grouped)
        #TAMBAH AMOUNT OTHER KLO DI INVOICE ADA
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        #TAMBAH AMOUNT OTHER KLO DI INVOICE ADA
        for oth in others_grouped:
            tax_lines += tax_lines.new(oth)
            
        self.tax_line_ids = tax_lines
        
        for tax_update in self.tax_line_ids:
            amount += tax_update.amount
        #AMOUNT + TAXES OR OTHER
        print ('=== amount + tax + amount_charges==', amount,amount_charges)
        self.amount = amount + amount_charges 
        return

#     @api.onchange('tax_line_ids')
#     def _onchange_tax_line_ids(self):
#         amount = 0.0
#         for line in self.tax_line_ids:
#             amount += line.amount
#         self.amount = amount
#         return
    
#     @api.onchange('invoice_line_ids')
#     def _onchange_invoice_line_ids(self):
#         taxes_grouped = self.get_taxes_values()
#         tax_lines = self.tax_line_ids.filtered('manual')
#         for tax in taxes_grouped.values():
#             tax_lines += tax_lines.new(tax)
#         self.tax_line_ids = tax_lines
#         return
    
    # def _prepare_account_move_line(self, line):
    #     data = super(AccountPayment, self)._prepare_account_move_line(line=line)
    #     #print ('---_prepare_account_move_line----',data)
    #     if line.move_id and line.move_id.amount_tax_wth:
    #         data['payment_line_wth_tax_ids'] = [(6, 0, [line.id for line in line.move_id.mapped('invoice_line_ids').mapped('invoice_line_wth_tax_ids')])]
    #         #[(0, 0, line.move_id.invoice_line_ids.invoice_line_wth_tax_ids)]
    #     return data
    
    
    def _get_payment_taxes_entry(self, tline):
        vals = super(AccountPayment, self)._get_payment_taxes_entry(tline=tline)
        payment = self
        company_currency = payment.company_id.currency_id
        #write_off_amount = line.writeoff_account_id and -line.payment_difference or 0.0
        #counterpart_amount = line.amount_to_pay * (payment.payment_type in ('outbound', 'transfer') and 1 or -1)
        if payment.currency_id == company_currency:
            # Single-currency.
            #balance = counterpart_amount
            #write_off_line_balance = write_off_amount
            tax_amount_currency = tline.amount
            #counterpart_amount = write_off_amount = 0.0
            currency_id = company_currency.id
        else:
            # Multi-currencies.
            #balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
            #write_off_line_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
            tax_amount_currency = payment.currency_id.with_context(force_rate=tline.amount)._convert(tline.amount, company_currency, payment.company_id, payment.date)
            currency_id = payment.currency_id.id
        #rec_pay_line_name = line.name
        if payment.payment_type == 'inbound':
            tline_amount = -tline.amount
        else:
            tline_amount = tline.amount
        #RECEIVABLE
        vals = {
            'name': tline.name,
            'amount_currency': tax_amount_currency if tline_amount > 0.0 else -tax_amount_currency,
            'currency_id': currency_id,
            'debit': abs(tline.amount) if tline_amount > 0.0 else 0.0,
            'credit': abs(tline.amount) if tline_amount < 0.0 else 0.0,
            'date_maturity': payment.payment_date,
            'partner_id': payment.partner_id.id,
            'account_id': tline.account_id.id,
            'payment_id': payment.id,
            #'account_id': payment.destination_account_id.id,
            #'payment_line_id': line.id,
        }
        #print ('===_get_payment_taxes_entry===',vals)
        return vals
    
#     def _create_payment_entry_multi(self, amount, invoice, move, line):
#         counterpart_aml, aml_to_reconcile = super(AccountPayment, self)._create_payment_entry_multi(amount=amount, invoice=invoice, move=move, line=line)
#         #print ('---counterpart_aml, aml_to_reconcile--',counterpart_aml, aml_to_reconcile)
#         aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
#         invoice_currency = invoice.currency_id
#         if self.tax_line_ids:# or line.payment_line_wth_tax_ids and line.amount_wth_tax:
#             #print ('----line-----',line.amount_wth_tax,line.amount)
#             if not invoice_currency:
#                 invoice_currency = line.currency_id
#             for tax in self.tax_line_ids:
#                 print ('===,line.amount_wth_tax===',tax.amount)
#                 #if tax.already_select_for_invoice == False:
#                 withholding_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
#                 amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date, force_rate=self.force_rate)._compute_amount_fields(tax.amount, invoice_currency, self.company_id.currency_id)[2:]
#                 #print ('--------ssss=----',amount_currency_wo, currency_id)
#                 # the writeoff debit and credit must be computed from the invoice residual in company currency
#                 # minus the payment amount in company currency, and not from the payment difference in the payment currency
#                 # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
#                 #total_residual_company_signed = line.move_id.residual_company_signed#sum(invoice.residual_company_signed for invoice in self.move_ids)
#                 #total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(line.amount_to_pay, self.company_id.currency_id)
#                 #if line.move_id.type in ['in_invoice', 'out_refund']:
#                 #    amount_wo = total_payment_company_signed - total_residual_company_signed
#                 #else:
#                 #    amount_wo = total_residual_company_signed - total_payment_company_signed
#                 amount_wo = tax.amount
#                 if self.payment_type == 'inbound':
#                     debit_wo = amount_wo < 0 and -amount_wo or 0.0
#                     credit_wo = amount_wo > 0 and amount_wo or 0.0
#                 else:
#                     debit_wo = amount_wo > 0 and amount_wo or 0.0
#                     credit_wo = amount_wo < 0 and -amount_wo or 0.0
# 
#                 withholding_line['name'] = _('Withholding Taxes %s'%tax.name) if tax.tax_id else tax.name
#                 withholding_line['account_id'] = tax.account_id.id
#                 withholding_line['payment_id'] = self.id
#                 withholding_line['debit'] = debit_wo
#                 withholding_line['credit'] = credit_wo
#                 withholding_line['amount_currency'] = amount_currency_wo
#                 withholding_line['currency_id'] = currency_id
#                 withholding_line = aml_obj.create(withholding_line)
#                 #print ('=====withholding_line====',withholding_line)
#                 tax.already_select_for_invoice = True
# #             if counterpart_aml['debit']:
# #                 counterpart_aml['debit'] += credit_wo - debit_wo
# #             if counterpart_aml['credit']:
# #                 counterpart_aml['credit'] += debit_wo - credit_wo
# #             counterpart_aml['amount_currency'] -= amount_currency_wo
#         return counterpart_aml, aml_to_reconcile
    

class AccountPaymentTax(models.Model):
    _inherit = "account.payment.tax"
    
    @api.depends('payment_id.register_ids')
    def _compute_base_amount(self):
        tax_grouped = {}
        for payment in self.mapped('payment_id'):
            tax_grouped[payment.id] = payment.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'account_analytic_id': tax.account_analytic_id.id,
                    'analytic_tag_ids': tax.analytic_tag_ids.ids or False,
                })
                if tax.payment_id and key in tax_grouped[tax.payment_id.id]:
                    tax.base = tax_grouped[tax.payment_id.id][key]['base']
                else:
                    _logger.warning('Tax Base Amount not computable probably due to a change in an underlying tax (%s).', tax.tax_id.name)

    #payment_id = fields.Many2one('account.payment', string='Payment', ondelete='cascade', index=True)
    #name = fields.Char(string='Description', required=True)
    # payment_line_id = fields.Many2one('account.payment.line', string='Payment Line', ondelete='restrict')
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    amount = fields.Monetary('Amount')
    amount_rounding = fields.Monetary('Amount Delta')
    amount_total = fields.Monetary(string="Amount Total", compute='_compute_amount_total')
    manual = fields.Boolean(default=True)
    #sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', store=True, readonly=True)
    base = fields.Monetary(string='Base', compute='_compute_base_amount', store=True)
    already_select_for_invoice = fields.Boolean(default=False)

    # def unlink(self):
    #     for otax in self:
    #         # if otax.state not in ('draft', 'cancel'):
    #         raise UserError(_('Cannot delete voucher(s) which are already opened or paid.'))
    #     return super(AccountPaymentTax, self).unlink()


    @api.depends('amount', 'amount_rounding')
    def _compute_amount_total(self):
        for tax_line in self:
            tax_line.amount_total = tax_line.amount + tax_line.amount_rounding
            
class account_payment_line(models.Model):
    _inherit = 'account.payment.line'

    payment_line_wth_tax_ids = fields.Many2many('account.tax',
        'account_payment_line_wht_tax', 'payment_line_id', 'tax_id',
        string='Wth Taxes', domain=[('type_tax_use','!=','none'), '|', ('active', '=', False), ('active', '=', True)])
    amount_wth_tax = fields.Monetary('Tax Amount', compute="_tax_calculate", store=False, readonly=True)  
    tax_type = fields.Char('Tax Categ', compute="_get_tax_type")
    

    @api.depends('payment_id', 'payment_id.journal_id')
    def _get_tax_type(self):
        for line in self:
            if line.payment_id.partner_type == 'customer':
                line.tax_type ='sale'
            if line.payment_id.partner_type == 'supplier':
                line.tax_type ='purchase'
            if line.payment_id.partner_type == False:
                line.tax_type ='none'
    
    
    @api.depends('amount_to_pay', 'payment_line_wth_tax_ids')
    def _tax_calculate(self):
        #qty_processed_per_product = defaultdict(lambda: 0)
        #grouped_lines = defaultdict(lambda: self.env['account.payment.line'])
        for line in self:
            if line.invoice_id:
                taxes = line.payment_line_wth_tax_ids.compute_all(line.invoice_id.amount_untaxed, line.payment_currency_id, 1.0, False, line.payment_id.partner_id)['taxes']
            else:
                taxes = line.payment_line_wth_tax_ids.compute_all(line.amount_to_pay, line.payment_currency_id, 1.0, False, line.payment_id.partner_id)['taxes']
            #print ('==taxes==',line.invoice_id,taxes)
            amount_wth_tax = 0.0
            for tax in taxes:
                amount_wth_tax += tax['amount']
            line.amount_wth_tax = amount_wth_tax
    