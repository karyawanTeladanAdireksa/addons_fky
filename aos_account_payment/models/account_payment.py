# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import threading
import math
from datetime import datetime,date
from odoo.tools.misc import profile

from odoo import models, fields, api, _, sql_db
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

CREATE = 0
UPDATE = 1
DELETE = 2
UNLINK = 3
LINK = 4
CLEAR = 5
SET = 6
#import pdpp.addons.decimal_precision as dp

# MAP_INVOICE_TYPE_PARTNER_TYPE = {
#     'out_invoice': 'customer',
#     'out_refund': 'customer',
#     'out_receipt': 'customer',
#     'in_invoice': 'supplier',
#     'in_refund': 'supplier',
#     'in_receipt': 'supplier',
# }

class AccountPayment(models.Model):
    _inherit = "account.payment"
        
    def _prepare_account_move_line(self, line):
        data = {
            'move_line_id': line.id,
            'date':line.date,
            'date_due':line.date_maturity or line.date,
            'type': line.debit and 'dr' or 'cr',
            'invoice_id': line.move_id.id,
            'name': line.move_id.name or line.name or '/',
        }
        company_currency = self.journal_id.company_id.currency_id
        payment_currency = self.currency_id or company_currency
        if line.currency_id and payment_currency==line.currency_id:
            data['amount_total'] = abs(line.amount_currency)
            data['residual'] = abs(line.amount_residual_currency)
            data['amount_to_pay'] = 0.0#abs(line.amount_residual_currency)
        else:
            #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
            data['amount_total'] = company_currency.compute(line.credit or line.debit or 0.0, payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
            data['residual'] = company_currency.compute(abs(line.amount_residual), payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx)
            data['amount_to_pay'] = 0.0#company_currency.compute(abs(line.amount_residual), payment_currency, round=False)#currency_pool.compute(cr, uid, company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0, context=ctx)
        #line.payment_selected_id = self.id
        return data
    
    def _prepare_account_move_line_low_level(self, lines):
        self.ensure_one()
        # data = {
        #     'move_line_id': line.id,
        #     'date':line.date,
        #     'date_due':line.date_maturity,
        #     'type': line.debit and 'dr' or 'cr',
        #     'invoice_id': line.move_id.id,
        #     'name': line.move_id.name or line.name or '/',
        # }
        qlines = lines.mapped(lambda r:(self.id,r.id,
                                   fields.Date.to_string(r.date),
                                   fields.Date.to_string(r.date_maturity) or fields.Date.to_string(r.date),
                                   r.debit,
                                   r.move_id.id,
                                   r.move_id.name or r.name or '/', 
                                   abs(r.amount_currency),
                                   abs(r.amount_residual_currency),
                                   0.0,))
        values = ", ".join(map(str,qlines))
        

        q = """INSERT INTO """+self.register_ids._table+""" (payment_id,move_line_id,date,date_due,type,invoice_id,name,amount_total,residual,amount_to_pay) VALUES %s""" % (values,)
        return q

    def _append_outstanding_line(self, domain, offset=0, limit=None):
        self.ensure_one()
        AccMoveLine = self.env['account.move.line']
        mls = AccMoveLine.search(domain,offset=offset,limit=limit)
        # new_lines = AccMoveLine
        # for line in mls:
        #     data = self._prepare_account_move_line(line)
        #     new_lines += AccMoveLine.new(data)
        if mls:
            q = self._prepare_account_move_line_low_level(mls)
            self.env.cr.execute(q)
            self.refresh()
    

    
    def _set_outstanding_lines(self, partner_id, account_id, currency_id, journal_id, payment_date):
        for payment in self:
            #payment.amount = 0.0
            # optimize #1
            # but in next line why it deleted if exist??so just delete it
            # payment.register_ids.write({'amount_to_pay': 0, 'writeoff_account_id': False, 'to_reconcile': False})
            # self.env.cr.execute("update "+payment.register_ids._table+" set amount_to_pay=0, writeoff_account_id=null, to_reconcile=null where id in %s",(tuple(self.register_ids.ids),))
            if payment.register_ids:
                # payment.register_ids.unlink()
                # optimization #2
                # delete by query
                # self.env.cr.execute("delete from "+self.register_ids._table+" where id in %s", (tuple(payment.register_ids.ids),))
                # FIXME: THIS NEED TO CHECK CONSTRAINS ON THE TABLE,, TEST WITH 1400+- record takes longer
                self.env.cr.execute("delete from "+payment.register_ids._table+" where payment_id = %s", (payment.id,))
                # payment.refresh()
            
            account_type = None
            if self.payment_type == 'outbound':
                account_type = 'payable'
            else:
                account_type = 'receivable'
            new_lines = self.env['account.payment.line']
            #SEARCH FOR MOVE LINE; RECEIVABLE/PAYABLE AND NOT FULL RECONCILED
            if account_id:
                # move_lines = self.env['account.move.line'].search([('account_id','=',account_id.id),('account_id.internal_type','=',account_type),('partner_id','=',partner_id.id),('reconciled','=',False),('move_id.state','=','posted')])
                dmn = [('account_id','=',account_id.id),('account_id.internal_type','=',account_type),('partner_id','=',partner_id.id),('reconciled','=',False),('move_id.state','=','posted')]
            else:
                dmn = [('account_id.internal_type','=',account_type),('partner_id','=',partner_id.id),('reconciled','=',False),('move_id.state','=','posted')]
                # move_lines = self.env['account.move.line'].search([('account_id.internal_type','=',account_type),('partner_id','=',partner_id.id),('reconciled','=',False),('move_id.state','=','posted')])
            
            #print ("==_set_outstanding_lines===",move_lines,account_id,account_type,partner_id)
            # optimization #3
            from math import ceil
            AccMoveLine = self.env['account.move.line']
            total = AccMoveLine.search_count(dmn)
            limit = 100
            pages = ceil(total/limit)
            # OLD
            # for line in move_lines:
            #     data = payment._prepare_account_move_line(line)
            #     new_line = new_lines.new(data)
            #     new_lines += new_line
            # END OLD

            # NEW
            # for x in range(0,pages):
            #     offset = x * limit
            #     payment.with_delay(description="Append invoices [offset:%s,limit:%s] to %s" % (offset,limit,self.display_name,)) \
            #         ._append_outstanding_line(dmn, offset, limit)
                
            payment._append_outstanding_line(dmn)
            # END NEW
            #payment.destination_account_id = account_id.id

            # DISABLED TO OPTIMIZE
            # payment.register_ids += new_lines
            #'invoice_ids': [(4, inv.id, None) for inv in self._get_invoices()]
            
    @api.depends('payment_type', 'amount', 'amount_charges')#, 'other_lines')
    def _compute_price(self):
        total_other = 0.0
        for payment in self:
            #for oth in payment.other_lines:
            #    total_other += oth.amount
            if payment.advance_type == 'cash':
                payment.amount_subtotal = payment.amount - payment.amount_charges - total_other
            else:
                payment.amount_subtotal = payment.amount + payment.amount_charges + total_other
            

    def _unlink_invoice_ids(self):
        for payment in self:
            payment.reconciled_invoice_ids = [(6, 0, [])]
            
    #('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled')
    #state = fields.Selection(selection_add=[('confirm', 'Confirm')])
    #register_date = fields.Date(string='Register Date', required=False, copy=False)    
    advance_type = fields.Selection([('invoice', 'Reconcile to Invoice'), 
                                     ('advance', 'Down Payment'), 
                                     ('advance_emp', 'Employee Advance'),
                                     ('receivable_emp','Employee Receivable')], default='invoice', string='Type')
    #BASE ACCOUNTING KIT
    # bank_reference = fields.Char(copy=False)
    # cheque_reference = fields.Char(copy=False)
    # effective_date = fields.Date('Effective Date',
    #                              help='Effective date of PDC', copy=False,
    #                              default=False)
    #BASE ACCOUNTING KIT
    payment_date = fields.Date(string='Posted Date', required=False, copy=False)
    force_rate = fields.Float('Rate Amount')
#     name = fields.Char(readonly=True, copy=False)
#     customer_account_id = fields.Many2one('account.account', string='Customer Account', domain=[('reconcile','=',True)])
#     supplier_account_id = fields.Many2one('account.account', string='Supplier Account', domain=[('reconcile','=',True)])
    # dest_account_id = fields.Many2one('account.account', string='Dest. Account', domain=[('reconcile','=',True)])
    #
    # destination_account_id = fields.Many2one(
    #     comodel_name='account.account',
    #     string='Destination Account',
    #     store=True, readonly=False,
    #     compute='_compute_destination_account_id',
    #     domain="[('user_type_id.type', 'in', ('receivable', 'payable')), ('company_id', '=', company_id)]",
    #     check_company=True)
    communication = fields.Char(string='Ref#')
    #register_ids = fields.One2many('account.payment.line', 'payment_id', copy=False, string='Register Invoice')
    residual_account_id = fields.Many2one('account.account', string='Residual Account', domain=[('deprecated','=',False)])
    notes = fields.Text('Notes')
    #amount_subtotal = fields.Monetary(string='Amount', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    amount_subtotal = fields.Float(string='Amount Total',
        store=True, readonly=True, compute='_compute_price', tracking=True)
    amount_charges = fields.Monetary(string='Amount Adm', required=False)
    charge_account_id = fields.Many2one('account.account', string='Account Adm')
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
    register_ids = fields.One2many('account.payment.line', 'payment_id', copy=False, string='Register Invoice')
    tax_line_ids = fields.One2many('account.payment.tax', 'payment_id', string='Tax Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
                    
    def action_payment_line_tree(self):
        action = self.env.ref('aos_account_payment.action_payment_line_tree').read()[0]
        action['context'] = {
            #'default_location_id': self.location_id.id,
            #'default_product_id': self.product_id.id,
            #'default_prod_lot_id': self.lot_id.id,
            #'default_package_id': self.package_id.id,
            'default_partner_id': self.partner_id.id,
            'default_payment_id': self.id,
        }
        return action
    
    @api.onchange('destination_journal_id')
    def _onchange_destination_journal_id(self):
        if self.destination_journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.destination_journal_id.available_payment_method_ids or self.journal_id.available_payment_method_ids
            payment_methods_list = payment_methods.ids

            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                # Ensure the domain will accept the provided default value
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False

            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods_list)]}}
        return {}
    
    @api.onchange('register_ids', 'amount_charges')
    def _onchange_register_ids(self):
        amount = amount_subtotal = 0.0
        amount_charges = self.amount_charges
        for line in self.register_ids:
            #if line.action:
            amount += line.amount_to_pay
            #if line.payment_difference and line.writeoff_account_id:
            #    amount += line.payment_difference
#         total_other = 0.0
#         for oth in self.other_lines:
#             total_other += oth.amount
#         if self.advance_type == 'cash':
#             amount_subtotal = amount - self.amount_charges - total_other
#         else:
#             amount_subtotal = amount + self.amount_charges + total_other
        self.amount = amount + amount_charges
        print ('===amount_charges===',amount,amount_charges)
#         self.amount_subtotal = amount_subtotal
        return
    
    def button_outstanding_all(self):
        #print "==button_outstanding=="
        for payment in self:
            #print ('===s==',payment.destination_account_id)
            account_id = payment.destination_account_id or False
            #print ('===button_outstanding_all===',payment.date,payment.payment_date)
            if payment.partner_id and payment.currency_id and payment.journal_id and payment.date:
                #payment._set_currency_rate()
                payment.with_context(reset=True)._set_outstanding_lines(payment.partner_id, account_id, payment.currency_id, payment.journal_id, payment.date)
                #payment._set_invoice_ids()
                #print "===payment==",payment.register_ids
                #payment.invoice_ids = [(4, reg.invoice_id.id, None) for reg in payment.register_ids()]
            payment.amount = 0.0
                
    def _get_outstanding_lines(self, partner_id, account_id, currency_id, journal_id, payment_date):
        self.ensure_one()
#         for payment in self:
#             if payment.register_ids:
#                 payment.register_ids.unlink()
        account_type = None
        if self.payment_type == 'outbound':
            account_type = 'payable'
        else:
            account_type = 'receivable'
#             new_lines = self.env['account.payment.line']
        #SEARCH FOR MOVE LINE; RECEIVABLE/PAYABLE AND NOT FULL RECONCILED
        if account_id:
            move_lines = self.env['account.move.line'].search([('account_id','=',account_id.id),('account_id.internal_type','=',account_type),('partner_id','=',partner_id.id),('reconciled','=',False),('move_id.state','=','posted')])
        else:
            move_lines = self.env['account.move.line'].search([('account_id.internal_type','=',account_type),('partner_id','=',partner_id.id),('reconciled','=',False),('move_id.state','=','posted')])
        #print ("==_set_outstanding_lines===",move_lines)
        return move_lines
        
    def button_outstanding(self):
        """ Opens a wizard to assign SN's name on each move lines.
        """
        self.ensure_one()
        action = self.env.ref('aos_account_payment.act_assign_account_invoice').read()[0]
        action['context'] = {
            #'default_product_id': self.product_id.id,
            #'default_move_id': self.id,
        }
        return action
    
    
    def _get_counterpart_fields(self, line):        
        payment = self
        company_currency = payment.company_id.currency_id
        #write_off_amount = line.writeoff_account_id and -line.payment_difference or line.payment_difference
        write_off_amount = (line.payment_difference if line.writeoff_account_id else 0) * (payment.payment_type in ('outbound', 'transfer') and 1 or -1)
        counterpart_amount = line.amount_to_pay * (payment.payment_type in ('outbound', 'transfer') and 1 or -1)
        if payment.currency_id == company_currency:
            # Single-currency.
            balance = counterpart_amount
            write_off_line_balance = write_off_amount
            #charge_amount_currency = 0.0
            #counterpart_amount = write_off_amount = write_off_amount
            currency_id = company_currency.id
        else:
            # Multi-currencies.
            balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.date)
            write_off_line_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.date)
            #charge_amount_currency = payment.currency_id.with_context(force_rate=payment.force_rate)._convert(payment.amount_charges, company_currency, payment.company_id, payment.register_date)
            currency_id = payment.currency_id.id
        #print ('===_get_counterpart_fields====',balance, write_off_line_balance, currency_id, counterpart_amount)
        return balance, write_off_line_balance, currency_id, counterpart_amount
    
    def _get_payment_taxes_entry(self, tline):
        vals = {}
        return vals

    def _get_amount_charges_lines(self):
        #balance, write_off_line_balance, charge_amount_currency, currency_id, counterpart_amount = self._get_counterpart_fields(line)
        payment = self
        company_currency = payment.company_id.currency_id
        #write_off_amount = line.writeoff_account_id and -line.payment_difference or 0.0
        #counterpart_amount = line.amount_to_pay * (payment.payment_type in ('outbound', 'transfer') and 1 or -1)
        if payment.currency_id == company_currency:
            # Single-currency.
            #balance = counterpart_amount
            #write_off_line_balance = write_off_amount
            charge_amount = -payment.amount_charges
            #counterpart_amount = write_off_amount = 0.0
            currency_id = company_currency.id
        else:
            # Multi-currencies.
            #balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
            #write_off_line_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
            charge_amount = -payment.currency_id.with_context(force_rate=payment.force_rate)._convert(payment.amount_charges, company_currency, payment.company_id, payment.date)
            currency_id = self.currency_id.id
        #rec_pay_line_name = line.name
        #POSISI BIAYA ADMIN
        #JIKA RECEIVABLE DAN BIAYA ADMIN MINUS (POSISIKAN DI DEBIT)
        if self.payment_type == 'inbound':
            charge_amount = charge_amount
            if payment.amount_charges < 0.0:
                #MINUS MENGURANGI BANK DI LETAKKAN DI DEBIT (MASUK BIAYA)
                debit_charges = abs(charge_amount)
                credit_charges = 0.0
                #charge_amount = charge_amount
                # charge_amount_currency = -payment.amount_charges
            else:
                #PLUS MENAMBAH BANK DI LETAKKAN DI CREDIT (MASUK PENDAPATAN)
                debit_charges = 0.0
                credit_charges = abs(charge_amount)
                #charge_amount = charge_amount
                # charge_amount_currency = -payment.amount_charges
        else:
            charge_amount = -charge_amount
            if payment.amount_charges > 0.0:
                debit_charges = abs(charge_amount)
                credit_charges = 0.0
                # charge_amount = -charge_amount
                # charge_amount_currency = -payment.amount_charges
            else:
                debit_charges = 0.0
                credit_charges = abs(charge_amount)
                # charge_amount = charge_amount
                # charge_amount_currency = -payment.amount_charges
        #print ('#JIKA PAYABLE DAN BIAYA ADMIN MINUS (POSISIKAN DI CREDIT)',currency_id,debit_charges,credit_charges,charge_amount_currency)
        vals = {
            'name': _('ADM CHARGE for %s') % payment.name,
            'amount_currency': charge_amount,# if payment.amount_charges < 0 else -charge_amount_currency,
            'currency_id': currency_id,
            'debit': debit_charges,#abs(payment.amount_charges) if payment.amount_charges < 0.0 else 0.0,
            'credit': credit_charges,#abs(payment.amount_charges) if payment.amount_charges > 0.0 else 0.0,
            'date_maturity': payment.payment_date,
            'partner_id': payment.partner_id.id,
            'account_id': payment.charge_account_id.id,
            'payment_id': payment.id,
            'is_payment_charge': True,
            #'account_id': payment.destination_account_id.id,
            #'payment_line_id': line.id,
        }
        #print ('==BIAYA ADMIN==',vals)
        return vals

    def _get_counterpart_charges_lines(self):
        # {
        #     'name': liquidity_line_name or default_line_name,
        #     'date_maturity': self.date,
        #     'amount_currency': liquidity_amount_currency,
        #     'currency_id': currency_id,
        #     'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
        #     'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
        #     'partner_id': self.partner_id.id,
        #     'account_id': self.outstanding_account_id.id,
        # }
        payment = self
        company_currency = payment.company_id.currency_id
        #write_off_amount = line.writeoff_account_id and -line.payment_difference or 0.0
        #counterpart_amount = line.amount_to_pay * (payment.payment_type in ('outbound', 'transfer') and 1 or -1)
        if payment.currency_id == company_currency:
            # Single-currency.
            #balance = counterpart_amount
            #write_off_line_balance = write_off_amount
            charge_amount_currency = payment.amount_charges
            #counterpart_amount = write_off_amount = 0.0
            currency_id = company_currency.id
        else:
            # Multi-currencies.
            #balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
            #write_off_line_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
            charge_amount_currency = payment.currency_id.with_context(force_rate=payment.force_rate)._convert(payment.amount_charges, company_currency, payment.company_id, payment.date)
            currency_id = self.currency_id.id
        #rec_pay_line_name = line.name
        #RECEIVABLE
        vals = {
            'name': _('ADM CHARGE for %s') % payment.name,
            'amount_currency': charge_amount_currency if currency_id else 0.0,
            'currency_id': currency_id,
            'debit': payment.amount_charges > 0.0 and payment.amount_charges or 0.0,
            'credit': payment.amount_charges < 0.0 and -payment.amount_charges or 0.0,
            'date_maturity': payment.payment_date,
            'partner_id': payment.partner_id.id,
            'account_id': payment.outstanding_account_id.id,
            'payment_id': payment.id,
            #'payment_line_id': line.id,
        }
        #print ('==a==',vals)
        return vals
    
    
    def _get_counterpart_lines(self, line):
        balance, write_off_line_balance, currency_id, counterpart_amount = self._get_counterpart_fields(line)
        # print ('==_get_counterpart_lines==',balance, write_off_line_balance, currency_id, counterpart_amount)
        rec_pay_line_name = line.name
        #RECEIVABLE
        vals = {
            'name': rec_pay_line_name,
            'amount_currency': counterpart_amount + write_off_line_balance if currency_id else 0.0,
            'currency_id': currency_id,
            'debit': balance + write_off_line_balance > 0.0 and balance + write_off_line_balance or 0.0,
            'credit': balance + write_off_line_balance < 0.0 and -balance - write_off_line_balance or 0.0,
            'date_maturity': self.date,
            'partner_id': self.partner_id.id,
            'account_id': line.move_line_id.account_id.id,
            'payment_id': self.id,
            'payment_line_id': line.id,
        }
        #print ('==_get_counterpart_lines==',counterpart_amount,write_off_line_balance)
        return vals
    
    def _get_counterpart_writeoff_lines(self, line):
        balance, write_off_line_balance, currency_id, counterpart_amount = self._get_counterpart_fields(line)
        #WRITEOFF
        #vals = {}
        #if write_off_line_balance and line.writeoff_account_id:
            # Write-off line.
        vals = {
            'name': 'Write-off %s' % line.name,
            'amount_currency': -write_off_line_balance,
            'currency_id': currency_id,
            'debit': write_off_line_balance < 0.0 and -write_off_line_balance or 0.0,
            'credit': write_off_line_balance > 0.0 and write_off_line_balance or 0.0,
            'date_maturity': self.payment_date,
            'partner_id': self.partner_id.id,
            'account_id': line.writeoff_account_id.id,
            'payment_id': self.id,
        }
        #print ('==b==',vals)
        return vals

    def _sanity_empty_vals_list(self, vals):
        newlines = []
        
        for l in vals:
            if l.get('debit')>0.0 or l.get('credit')>0.0:
                newlines.append(l)
        if not newlines:
            if len(vals) > 3 and len(vals) > len(self.register_ids.filtered(lambda r:r.amount_to_pay)):
                # only take 3 top
                return vals[:3]
            return vals
        
        return newlines

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        #CHANGE THE BASE DEF _prepare_move_line_default_vals
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        # print ('==_prepare_move_line_default_vals==',self._context,write_off_line_vals)
        self.ensure_one()
        company_currency = self.company_id.currency_id
        if isinstance(write_off_line_vals, list) and write_off_line_vals:
            line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        else:
            write_off_line_vals = write_off_line_vals or {}
            # company_currency = self.company_id.currency_id
            if not self.outstanding_account_id:
                raise UserError(_(
                    "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                    self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
                write_off_amount_currency *= -1
            else:
                liquidity_amount_currency = write_off_amount_currency = 0.0
            
            if self._context.get('reset'):
                liquidity_amount_currency = 0.0
            if not self.date:
                self.date = fields.date.today()
                #raise UserError(_("A payment must have Date"))
            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            if self.is_internal_transfer:
                if self.payment_type == 'inbound':
                    liquidity_line_name = _('Transfer to %s', self.journal_id.name)
                else: # payment.payment_type == 'outbound':
                    liquidity_line_name = _('Transfer from %s', self.journal_id.name)
            else:
                liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = self._prepare_payment_display_name()

            default_line_name = self.env['account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                self.amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )
            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                # {
                #     'name': self.payment_reference or default_line_name,
                #     'date_maturity': self.date,
                #     'amount_currency': counterpart_amount_currency,
                #     'currency_id': currency_id,
                #     'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                #     'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                #     'partner_id': self.partner_id.id,
                #     'account_id': self.destination_account_id.id,
                # },
            ]
            #print ('--==line_vals_list==--11-',line_vals_list)

            #=======================JOURNAL CHARGES=============================
            if self.amount_charges and self.charge_account_id:
                line_vals_list.append(self._get_amount_charges_lines())
                # line_vals_list.append(self._get_counterpart_charges_lines())
                if self.currency_id == company_currency:
                    # Single-currency.
                    #balance = counterpart_amount
                    #write_off_line_balance = write_off_amount
                    charge_amount_currency = self.amount_charges
                    #counterpart_amount = write_off_amount = 0.0
                    currency_id = company_currency.id
                else:
                    # Multi-currencies.
                    #balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                    #write_off_line_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                    charge_amount_currency = self.currency_id.with_context(force_rate=self.force_rate)._convert(self.amount_charges, company_currency, self.company_id, self.date)
                    currency_id = self.currency_id.id
                # print ('==amount_charges==',counterpart_amount_currency+self.amount_charges,counterpart_balance+charge_amount_currency)
                counterpart_amount_currency = counterpart_amount_currency + self.amount_charges
                counterpart_balance = counterpart_balance + charge_amount_currency
            #==================get Receivable / Payable. on register lines==========
            if self.register_ids:
                for rline in self.register_ids:#.filtered(lambda pl: pl.amount_to_pay or pl.writeoff_account_id):
                    line_vals_list.append(self._get_counterpart_lines(rline))
                    #IF WRITE OF ON LINES
                    if rline.payment_difference and rline.writeoff_account_id:
                        line_vals_list.append(self._get_counterpart_writeoff_lines(rline))
            else:
                line_vals_list.append(
                # Receivable / Payable. TAKE HERE
                {   
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                })
            if not self.currency_id.is_zero(write_off_amount_currency) and not self.register_ids:
                # Write-off line.
                line_vals_list.append({
                    'name': write_off_line_vals.get('name') or default_line_name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': write_off_line_vals.get('account_id'),
                })
            #=======================JOURNAL TAXES & EXPENSES=============================
            if self.tax_line_ids:
                for tline in self.tax_line_ids:
                    #_get_counterpart_lines
                    #print ('tax')
                    line_vals_list.append(self._get_payment_taxes_entry(tline))
                    #line_vals_list.append(self._get_counterpart_lines_taxes_entry(tline))
                #line_vals_list.append(self._get_payment_taxes_entry())
            #===================================================================
            # print ('22==line_vals_list==22',line_vals_list)
            line_vals_list = self._sanity_empty_vals_list(line_vals_list)
            #print ('==line_vals_list==',line_vals_list)
            #contains_adm = [item for item in line_vals_list if 'ADM' in str(item.values())]
            debit_total = sum(item['debit'] for item in line_vals_list)
            credit_total = sum(item['credit'] for item in line_vals_list)
            contains_adm = [item for item in line_vals_list if 'ADM CHARGE for ' in str(item.values())]
            # print('====ADM DISC=BEFORE===',contains_adm)
            if contains_adm:
                # print ('=containt=',contains_adm[0]['debit'],contains_adm[0]['credit'])
                if contains_adm[0]['debit']:
                    contains_adm[0].update({'debit': contains_adm[0]['debit'] - (debit_total - credit_total)})
                else:
                    contains_adm[0].update({'credit': contains_adm[0]['credit'] - (credit_total - debit_total)})
            # print('====ADM DISC=AFTER===',contains_adm)
            print ('==line_vals_list==',line_vals_list)
        return line_vals_list
    
    # -------------------------------------------------------------------------
    # SYNCHRONIZATION GANTI FUNGSI ASLI BIAR GA NGEBLOK account.payment <-> account.move
    # -------------------------------------------------------------------------

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # if len(liquidity_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one outstanding payments/receipts account.",
                #         move.display_name,
                #     ))

                # if len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one receivable/payable account (with an exception of "
                #         "internal transfers).",
                #         move.display_name,
                #     ))

                # if writeoff_lines and len(writeoff_lines.account_id) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, "
                #         "all optional journal items must share the same account.",
                #         move.display_name,
                #     ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same partner.",
                        move.display_name,
                    ))

                # if counterpart_lines.account_id.user_type_id.mapped('type') == 'receivable':
                #     partner_type = 'customer'
                # else:
                #     partner_type = 'supplier'

                if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines[0].amount_currency if len(liquidity_lines) > 1 else liquidity_lines.amount_currency
                #JANGAN UPDATE KLO CURRRENCY ILANG
                if liquidity_lines.currency_id:
                    move_vals_to_write.update({
                        'currency_id': liquidity_lines.currency_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    payment_vals_to_write.update({
                        'amount': abs(liquidity_amount),
                        'partner_type': partner_type,
                        'currency_id': liquidity_lines.currency_id.id,
                        'destination_account_id': counterpart_lines.account_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    if liquidity_amount > 0.0:
                        payment_vals_to_write.update({'payment_type': 'inbound'})
                    elif liquidity_amount < 0.0:
                        payment_vals_to_write.update({'payment_type': 'outbound'})
            #print ('==move_vals_to_write==',move_vals_to_write,payment_vals_to_write)
            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))
    
    def _execute_synchronize_to_moves_lines(self, lines):
        to_create = []
        to_update = []
        to_delete = []

        for l in lines:
            # l ==> (0,0,{})
            # l ==> (1,int id,{})
            # l ==> (2,int id)
            # l ==> (3,int id)
            # l ==> (4,int id)
            # l ==> (5,0)
            # l ==> (6,0,[ids...])
            if l[0]==CREATE:
                to_create.append(l[2])
            elif l[0]==UPDATE:
                to_update.append(l)
            elif l[0]==DELETE:
                to_delete.append(l[1])
            else:
                raise UserError("Invalid command set")
        fs = {}
        values = []
        vals_create = []
        default_values = self.move_id.line_ids[0].default_get(list(dict(self.move_id.line_ids._fields).keys()))
        rel_fields = ['company_currency_id','company_id',
                        'journal_id',
                        'parent_state',
                        'ref',
                        'date',
                        'move_name',
                        # 'account_root_id',
                        # 'payment_id',
                        # 'statement_line_id',
                        # 'statement_id',
                        ]
        default_fields = rel_fields + list(default_values.keys())
        rel_fields_val = [self.move_id.company_currency_id.id,
                            self.move_id.company_id.id,
                            self.move_id.journal_id.id, self.move_id.state, self.move_id.ref,fields.Date.to_string(self.move_id.date),self.move_id.name,]
        default_vals = rel_fields_val + [x for i,x in default_values.items()]
        
        
        for c in to_create:
            keys = tuple(c.keys())
            if fs.get(keys):
                # append
                pass
            else:
                # create new
                fs[keys] = []
            re_default_fields = []
            re_default_values = []
            for df in default_fields:
                if df not in list(keys):
                    re_default_fields.append(df)
                    dvv = df in default_values
                    if dvv:
                        re_default_values.append(default_values[df])    
                    elif df in rel_fields:
                        curr = 0
                        for r in rel_fields:
                            if df == r:
                                break
                            curr += 1
                        re_default_values.append(rel_fields_val[curr])
            if re_default_fields:
                default_fields = re_default_fields
                default_vals = re_default_values
            val_create = [self.move_id.id] + default_vals #first column
            for f in keys:
                val = c.get(f)
                if type(val) == datetime:
                    val = fields.Datetime.to_string(val)
                elif type(val) == date:
                    val = fields.Date.to_string(val)
                val_create.append(val)

            fs[keys].append(tuple(val_create))
        for key,val in fs.items():
            ff = ['move_id'] + default_fields + list(key)
            # each field combination
            q_create = ("INSERT INTO account_move_line (%s) VALUES %s" % (",".join(ff), ", ".join(map(str,val)),)).replace('None','null').replace('False','null')
            self.env.cr.execute(q_create)
            self.refresh()
        
        if to_update:
            # self.move_id.write({'line_ids':to_update})
            for u in to_update:
                vs = []
                for i,v in u[2].items():
                    uv = v
                    if type(uv)==date:
                        uv = fields.Date.to_string(uv)
                    elif type(uv)==datetime:
                        uv = fields.Datetime.to_string(uv)
                    if type(uv)==str:
                        vs.append("%s='%s'" % (i,uv))
                    else:
                        vs.append("%s=%s" % (i,uv))
                if vs:
                    q = "update account_move_line set %s" % (", ".join(vs)) 
                    q += " where id = %s"
                    self._cr.execute(q, (u[1],))

        if to_delete:
            self.env['account.move.line'].browse(to_delete).unlink()
        
        pass
            
    def _synchronize_to_moves_new(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return
        #===============================================================================
        # ADD FIELDS register_ids
        #===============================================================================
        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'journal_id', 'register_ids', 'tax_line_ids',
            'amount_charges','charge_account_id'
        )):
            return
    
        for pay in self.with_context(skip_account_move_synchronization=True):
            #pay.register_ids.write({'amount_to_pay': 0, 'writeoff_account_id': False, 'to_reconcile': False})
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
            #print ('==_synchronize_to_moves==',liquidity_lines.balance, counterpart_lines.balance, writeoff_lines.balance)
            
            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.
    
            if liquidity_lines and counterpart_lines and writeoff_lines.filtered(lambda ml: not ml.is_payment_charge):
    
                counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))
    
                # To be consistent with the payment_difference made in account.payment.register,
                # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                # Since the write is already done at this point, we need to base the computation on accounting values.
                if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                    sign = -1
                else:
                    sign = 1
                writeoff_amount = abs(writeoff_amount) * sign
    
                write_off_line_vals = {
                    'name': writeoff_lines[0].name,
                    'amount': writeoff_amount,
                    'account_id': writeoff_lines[0].account_id.id,
                }
            else:
                write_off_line_vals = {}
            #print ('====write_off_line_vals===',write_off_line_vals)
            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
            #print ('==line_vals_list==',line_vals_list)
            
            # line_ids_commands = [
            #     (1, liquidity_lines.id, line_vals_list[0]),
            #     (1, counterpart_lines.id, line_vals_list[1]),
            # ]
    
            line_ids_commands = []
            if len(liquidity_lines) == 1:
                line_ids_commands.append((1, liquidity_lines.id, line_vals_list[0]))
            else:
                for line in liquidity_lines:
                    line_ids_commands.append((2, line.id, 0))
                line_ids_commands.append((0, 0, line_vals_list[0]))
            
            if len(counterpart_lines) == 1:
                line_ids_commands.append((1, counterpart_lines.id, line_vals_list[1]))
            else:
                for line in counterpart_lines:
                    line_ids_commands.append((2, line.id, 0))
                #===========================================================
                # MODIFY THIS LINE
                #===========================================================
                line_ids_commands.append((0, 0, line_vals_list[1])) if len(line_vals_list) > 1 else line_ids_commands
                #===========================================================
    
            for line in writeoff_lines:
                line_ids_commands.append((2, line.id))
    
            for extra_line_vals in line_vals_list[2:]:
                line_ids_commands.append((0, 0, extra_line_vals))
    
            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.
            #print ('==line_ids_commands==',line_ids_commands,counterpart_lines)
            # optimization #4
            # add into query 
            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                # 'line_ids': line_ids_commands, # optimized next line
            })
            pay._execute_synchronize_to_moves_lines(line_ids_commands)
            #print('okeee')

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return
        #===============================================================================
        # ADD FIELDS register_ids
        #===============================================================================
        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'journal_id', 'register_ids', 'tax_line_ids',
            'amount_charges','charge_account_id'
        )):
            return
    
        for pay in self.with_context(skip_account_move_synchronization=True):
            #pay.register_ids.write({'amount_to_pay': 0, 'writeoff_account_id': False, 'to_reconcile': False})
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
            #print ('==_synchronize_to_moves==',liquidity_lines.balance, counterpart_lines.balance, writeoff_lines.balance)
            
            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.
    
            if liquidity_lines and counterpart_lines and writeoff_lines.filtered(lambda ml: not ml.is_payment_charge):
    
                counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))
    
                # To be consistent with the payment_difference made in account.payment.register,
                # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                # Since the write is already done at this point, we need to base the computation on accounting values.
                if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                    sign = -1
                else:
                    sign = 1
                writeoff_amount = abs(writeoff_amount) * sign
    
                write_off_line_vals = {
                    'name': writeoff_lines[0].name,
                    'amount': writeoff_amount,
                    'account_id': writeoff_lines[0].account_id.id,
                }
            else:
                write_off_line_vals = {}
            #print ('====write_off_line_vals===',write_off_line_vals)
            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
            #print ('==line_vals_list==',line_vals_list)
            
            # line_ids_commands = [
            #     (1, liquidity_lines.id, line_vals_list[0]),
            #     (1, counterpart_lines.id, line_vals_list[1]),
            # ]
    
            line_ids_commands = []
            if len(liquidity_lines) == 1:
                line_ids_commands.append((1, liquidity_lines.id, line_vals_list[0]))
            else:
                for line in liquidity_lines:
                    line_ids_commands.append((2, line.id, 0))
                line_ids_commands.append((0, 0, line_vals_list[0]))
            
            if len(counterpart_lines) == 1:
                line_ids_commands.append((1, counterpart_lines.id, line_vals_list[1]))
            else:
                for line in counterpart_lines:
                    line_ids_commands.append((2, line.id, 0))
                #===========================================================
                # MODIFY THIS LINE
                #===========================================================
                line_ids_commands.append((0, 0, line_vals_list[1])) if len(line_vals_list) > 1 else line_ids_commands
                #===========================================================
    
            for line in writeoff_lines:
                line_ids_commands.append((2, line.id))
    
            for extra_line_vals in line_vals_list[2:]:
                line_ids_commands.append((0, 0, extra_line_vals))
    
            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.
            #print ('==line_ids_commands==',line_ids_commands,counterpart_lines)
            # optimization #4
            # add into query 
            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands, # optimized next line
            })
            # pay._execute_synchronize_to_moves_lines(line_ids_commands)
            # print('okeee')
                
    # @api.onchange('destination_journal_id')
    # def _onchange_destination_journal(self):
    #     if self.destination_journal_id:
    #         print ('==dest=')
    #         self.destination_account_id = self.destination_journal_id.default_debit_account_id and self.destination_journal_id.default_debit_account_id.id or self.destination_journal_id.default_credit_account_id or self.destination_journal_id.default_debit_account_id.id or False               
    #     @api.model_cr

    # def init(self):
    #     _logger.info("start unlink.zero.register.line function...")
    #     #precision_digits = max(6, self.env.ref('product.decimal_product_uom').digits * 2)
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE FUNCTION public.UnlinkZeroRegisterLine(rlines integer)
    #         RETURNS void AS
    #         $BODY$
    #         DECLARE
    #             abs RECORD;
    #         BEGIN
    #             DELETE FROM account_payment_line WHERE id = rlines;
    #         END;
    #         $BODY$
    #         LANGUAGE plpgsql VOLATILE
    #         COST 100;
    #     """)
    #     _logger.info("end of unlink.zero.register.line function...")

#     @api.multi
#     def _compute_move_line_lots(self):
#         try:
#             new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
#             uid, context = self.env.uid, self.env.context
#             with api.Environment.manage():
#                 self.env = api.Environment(new_cr, uid, context)
#                 #lots = self.env['stock.production.lot'].browse(context.get('active_ids'))
#                 #for lot in self.lot_id.id:
#                 if self.lot_id:
#                     self.env.cr.execute("select UpdateLastQuant(%s)" % self.lot_id.id)
#                     new_cr.commit()
#         finally:
#             self.env.cr.close()

    # def _do_zero_unlink(self):
    #     try:
    #         print ('===START===')
    #         new_cr = sql_db.db_connect(self.env.cr.dbname).cursor() 
    #         # uid, context = self.env.uid, self.env.context
    #         unlink_lines = [eline.id for eline in self.register_ids.filtered(lambda l: l.amount_to_pay == 0)]
    #         # with api.Environment.manage():
    #         #     self.env = api.Environment(new_cr, uid, context)
    #             #if self.lot_id:
    #         for eline in unlink_lines:
    #             print ('==eline==',eline)
    #             new_cr.execute("select UnlinkZeroRegisterLine(%s)" % eline)
    #             new_cr.commit()
    #         #self.env.cr.execute("select UnlinkZeroRegisterLine(%s)" % (tuple(unlink_lines),))
    #         # unlink_lines = [eline.id for eline in self.register_ids.filtered(lambda l: l.amount_to_pay == 0)]
    #         # if not unlink_lines:
    #         #     raise ValidationError(_('No zero Amount for Allocation'))
    #         # new_cr.execute('delete from account_payment_line where id in %s', (tuple(unlink_lines[:1000]),))
    #         print ('===END===')
    #         #new_cr.commit()
    #     finally:
    #         self.env.cr.close()

    def action_unlink(self):
        for payment in self:
            print ('--action_unlink--')
            #thread_start = threading.Thread(target=payment._do_zero_unlink())
            #thread_start.start()
        return True
            
    
    def action_post(self):
        #self.move_id._post(soft=False)
        #result = super(AccountPayment, self).action_post()
        unlink_elines = self.env['account.payment.line']
        unlink_mlines = self.env['account.move.line']
        for eline in self.register_ids:#.filtered(lambda a: a.amount_to_pay or a.writeoff_account_id):
            if eline.amount_to_pay == 0 and not eline.writeoff_account_id:
                #print ('===TO-DELETE===',eline,eline.amount_to_pay,eline.amount_to_pay)
                self.move_id.line_ids.filtered(lambda a: a.payment_line_id == eline and abs(a.debit) - abs(a.credit) == 0).unlink()
                # eline.unlink()
                self._cr.execute('delete from '+eline._table+ ' where id in %s', (tuple(eline.ids),))
        result = super(AccountPayment, self).action_post()
        for rline in self.register_ids:
            #print ('===TO-RECONCILE=11=',rline.move_line_id,self.move_id.line_ids.filtered(lambda i: i.payment_line_id == rline and not rline.move_line_id.reconciled))
            rlines = rline.move_line_id + self.move_id.line_ids.filtered(lambda i: i.payment_line_id == rline and not rline.move_line_id.reconciled)
            #print ('===TO-RECONCILE=22=',rlines)
            if self.move_id.line_ids.filtered(lambda i: i.payment_line_id == rline and not rline.move_line_id.reconciled):
                rlines.reconcile()
                #unlink_elines += eline
                #unlink_mlines += self.move_id.line_ids.filtered(lambda a: a.payment_line_id == eline and abs(a.debit) - abs(a.credit) == 0)
            #print ('==action_post==',unlink_elines,unlink_mlines,rlines)
        #unlink_elines.unlink()
        #unlink_mlines.unlink()
        #result = super(AccountPayment, self).action_post()
        # for rline in self.register_ids:#.filtered(lambda a: a.amount_to_pay or a.writeoff_account_id):
        #     if rline.amount_to_pay or rline.writeoff_account_id:
        #         rlines = rline.move_line_id + self.move_id.line_ids.filtered(lambda i: i.payment_line_id == rline and not eline.move_line_id.reconciled)
        #         rlines.reconcile()
        #rlines.reconcile()
        return result
    
    def action_cancel(self):
        ''' draft -> cancelled '''
        #self.move_id.button_cancel()
        vals = super(AccountPayment, self).action_cancel()
        self._unlink_invoice_ids()
        return vals
        
    def action_draft(self):
        print (''' posted -> draft ''')
        #self.move_id.button_draft()
        vals = super(AccountPayment, self).action_draft()
        if self.register_ids:
            self.register_ids.filtered(lambda a: a.amount_to_pay).mapped('move_line_id').remove_move_reconcile()
        return vals
    
class AccountPaymentLine(models.Model):
    _name = 'account.payment.line'
    _description = 'Account Payment Line'
    
    @api.depends('move_line_id', 'invoice_id', 'amount_total', 'residual', 'amount_to_pay', 'payment_id.date', 'currency_id')
    def _compute_payment_difference(self):
        for line in self:
            line.payment_difference = line.residual - line.amount_to_pay
        
        
    @api.depends('invoice_id', 'move_line_id')
    def _compute_invoice_currency(self):
        for line in self:
            if line.invoice_id and line.invoice_id.currency_id:
                line.move_currency_id = line.invoice_id.currency_id.id
            else:
                line.move_currency_id = line.move_line_id.currency_id.id
    
    #payment_line_id = fields.Many2one('account.payment.line', string='Payment Line', ondelete='restrict')
    move_line_id = fields.Many2one('account.move.line', string='Move Line', domain="[('account_id.user_type_id.type','in',('receivable','payable'))]")
    move_currency_id = fields.Many2one('res.currency', string='Invoice Currency', compute='_compute_invoice_currency',)
    date = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    type = fields.Selection([('dr', 'Debit'),('cr','Credit')], 'Type')
    payment_id = fields.Many2one('account.payment', string='Payment', index=True)
    payment_currency_id = fields.Many2one('res.currency', string='Currency')
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', string='Currency')
    name = fields.Char(string='Description', required=True)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    amount_total = fields.Float('Original Amount', required=True, digits='Product Price')
    residual = fields.Float('Outstanding Amount', required=True, digits='Product Price')
    reconcile = fields.Boolean('Full Payment')
    amount_to_pay = fields.Float('Allocation', required=True, digits='Product Price')
    statement_line_id = fields.Many2one('account.bank.statement.line', string='Statement Line')
    payment_difference = fields.Monetary(compute='_compute_payment_difference', string='Payment Difference', readonly=True, store=True)
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid'),
                                                    #('reconcile_multi', 'Fully payment with another payment')
                                                    ], 
                                                   default='open', string="Write-off", copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Write-off Account", domain=[('deprecated', '=', False)], copy=False)
    to_reconcile = fields.Boolean('To Pay')
    
#     @api.onchange('action')
#     def _onchange_action(self):
#         self.amount_to_pay = self.action and self.residual or 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            iline = self._compute_payment_line_id(self.env['account.move.line'].browse(vals['move_line_id']))
            vals['name'] = iline['name']
            vals['move_line_id'] = iline['move_line_id']
            vals['invoice_id'] = iline['invoice_id']
            vals['date'] = iline['date']
            vals['date_due'] = iline.get('date_due') and iline['date_due'] or iline['date']
            vals['amount_total'] = iline['amount_total']
            if not self.env.context.get('wizard_register'):
                vals['residual'] = iline['residual']
            #line.invoice_id.move_type in ['in_invoice', 'out_refund'] and 'cr' or 'dr'
        #print ('===vals_list==',vals_list)
        lines = super(AccountPaymentLine, self).create(vals_list)
        return lines

    # @api.model
    # def create(self, values):
    #     print ('====valuess===',values)
    #     if values.get('move_line_id'):
    #         print ('===self==')
    #         line = self.new(values)
    #         iline = line._compute_payment_line_id(self.env['account.move.line'].browse(values.get('move_line_id')))
    #         values['name'] = iline['name']
    #         values['move_line_id'] = iline['move_line_id']
    #         values['invoice_id'] = iline['invoice_id']
    #         values['date'] = iline['date']
    #         values['date_due'] = iline['date_due']
    #         values['amount_total'] = iline['amount_total']
    #         values['residual'] = iline['residual']
    #     print ('==values==',values)
    #     return super(account_payment_line, self).create(values)

    def _compute_payment_line_id(self, move_line):
        invoice = move_line.move_id
        # self.move_line_id = move_line
        # self.invoice_id = invoice
        # self.date = invoice.invoice_date
        # self.date_due = invoice.invoice_date_due
        # self.name = invoice.name
        # self.amount_total = invoice.amount_total
        # self.residual = invoice.amount_residual
        return {
            'name': invoice.name,
            'move_line_id': move_line.id,
            'invoice_id': invoice.id,
            'date': invoice.invoice_date,
            'date_due': invoice.invoice_date_due or invoice.invoice_date,
            'amount_total': invoice.amount_total,
            'residual': invoice.amount_residual,
        }

    @api.onchange('to_reconcile')
    def _onchange_to_reconcile(self):
        # if not self.to_reconcile:
        #     return
        amount_to_pay = self.residual if self.to_reconcile else 0.0
        # if self.to_reconcile and self.invoice_id.amount_others:
        #     amount_to_pay += self.invoice_id.amount_others
        self.amount_to_pay = amount_to_pay
        
    def _prepare_statement_line_entry(self, payment, statement):
        #print "===payment===",payment.name
        values = {
            'statement_id': statement.id,
            'payment_line_id': self.id,
            'date': payment.date,
            'name': self.invoice_id.number or self.move_line_id.name or '/', 
            'partner_id': payment.partner_id.id,
            'ref': payment.name,
            'amount': self.amount_to_pay,
        }
        return values
    
class account_move_line(models.Model):
    _inherit = 'account.move.line'
    
    payment_line_id = fields.Many2one('account.payment.line', string='Payment Line')
    is_payment_charge = fields.Boolean(default=False)
    #payment_selected_id = fields.Many2one('account.payment', string="Payment Line")
    
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        #print ('==_name_search=11=',name,operator,self.env.context)
        if operator == 'ilike':
            domain = ['|', '|',
                    ('name', 'ilike', name),
                    ('move_id', 'ilike', name),
                    ('product_id', 'ilike', name)]
            #print ('==domain=11',domain)
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        elif operator == '=':
            domain = [('account_id.user_type_id.type','in',('payable', 'receivable')),('move_id.ref', '=', name)]
            #print ('==domain=22',domain,args)
            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        #print ('==_name_search=22=',name)
        return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

class AccountPaymentTax(models.Model):
    _name = "account.payment.tax"
    _description = "Payment Tax"
    _order = 'sequence'
    
    name = fields.Char(string='Description', required=True)
    payment_id = fields.Many2one('account.payment', string='Payment', ondelete='cascade', index=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")