from odoo import models,api,fields,_
from odoo.exceptions import UserError
from odoo.tools import float_compare
import json
class AccountMove(models.Model):
    _inherit = "account.move"

    area_id = fields.Many2one("customer.area", related="partner_id.group_id.area_id")
    customer_group_id = fields.Many2one("adireksa.customer.target", string="Customer Group",related="partner_id.group_id",store=True)
    group_class_id = fields.Many2one('cashback.class.group',string="Group Class",related='customer_group_id.group_class_id')
    saldo_cashback = fields.Float('Saldo Cashback',compute="_compute_saldo_cashback")
    discount_total = fields.Monetary(string="Discount Total",compute="_compute_total_value",store=True)
    cashback_total = fields.Monetary(string="Cashback Total")
    discount_total_pivot = fields.Monetary(string="Discount Total")
    cashback_total_pivot = fields.Monetary(string="Cashback Total")
    bool_claim = fields.Boolean(compute="_compute_bool_claim")

    # def _action_set_group_target(self):
    #     self = self.env['account.move'].search([('group_ids','=',False),('move_type','not in',['in_invoice','in_refund','entry'])])
    #     self.compute_group_id()
    #     return True




    def cashback_pay_invoice(self):
        group_id = self.partner_id.group_id
        rule_id = self.env['cashback.rule'].search([('company_id','=',self.company_id.id)])
        if self.move_type != 'out_invoice':
            return
        if group_id and rule_id :
            used_rule = rule_id.line_ids .filtered(lambda x:x.trigger == 'invoice')   
            mcc_id = self.env['master.customer.cashback'].search([('group_id','=',group_id.id),('state','=','confirm')])
            total = 0
            data_line = used_rule.line_level_id
            days_range = data_line.mapped('days_before')
            days = self._context.get('payment_date') - self.invoice_date
            if days.days not in days_range:
                days_range.append(days.days)
                days_range.sort()
                index = days_range.index(days.days)
                if index != 0 :
                    used_range = days_range[index - 1]
                    data_used = data_line.filtered(lambda x:x.days_before == used_range)
                    total = (data_used.formula / 100) * (self.amount_total)
                    if self._context.get('payment'):
                        try :
                            amount = json.loads(self.invoice_payments_widget).get('content')[-1].get('amount')
                        except:
                            amount = self._context.get('payment').amount
                        total = (data_used.formula / 100) * (amount)
                    if self._context.get('payment') and self._context.get('to_pay'):
                        total = (data_used.formula / 100) * (self._context.get('to_pay'))
                    cashback = self.env['cashback.invoice'].create({
                        'name':self.env['ir.sequence'].next_by_code('cashback.invoice'),
                        'invoice_ids' : self.ids,
                        'company_id':self.company_id.id
                    })
                else :
                    used_range = days_range[index]
                    data_used = data_line.filtered(lambda x:x.days_before == used_range)
                    total = (data_used.formula / 100) * (self.amount_total)
                    if self._context.get('payment'):
                        try :
                            amount = json.loads(self.invoice_payments_widget).get('content')[-1].get('amount')
                        except:
                            amount = self._context.get('payment').amount
                        total = (data_used.formula / 100) * (amount)
                    if self._context.get('payment') and self._context.get('to_pay'):
                        total = (data_used.formula / 100) * (self._context.get('to_pay'))
                    cashback = self.env['cashback.invoice'].create({
                        'name':self.env['ir.sequence'].next_by_code('cashback.invoice'),
                        'invoice_ids' : self.ids,
                        'company_id':self.company_id.id
                    })
            else :
                index = days_range.index(days.days)
                used_range = days_range[index]
                data_used = data_line.filtered(lambda x:x.days_before == used_range)
                total = (data_used.formula / 100) * (self.amount_total)
                if self._context.get('payment'):
                        try :
                            amount = json.loads(self.invoice_payments_widget).get('content')[-1].get('amount')
                        except:
                            amount = self._context.get('payment').amount
                        total = (data_used.formula / 100) * (amount)
                if self._context.get('payment') and self._context.get('to_pay'):
                        total = (data_used.formula / 100) * (self._context.get('to_pay'))
                cashback = self.env['cashback.invoice'].create({
                    'name':self.env['ir.sequence'].next_by_code('cashback.invoice'),
                    'invoice_ids' : self.ids,
                    'company_id':self.company_id.id
                })
            if used_rule :
                if self.invoice_payment_term_id.cash_payment !=  True :
                    amount = str(self.amount_total) if not self._context.get('payment') else str(self._context.get('payment').amount)
                    try :
                        amount = str(json.loads(self.invoice_payments_widget).get('content')[-1].get('amount'))
                    except:
                        amount = str(self.amount_total) if not self._context.get('payment') else str(self._context.get('payment').amount)
                    if self._context.get('to_pay') :
                        amount = str(self._context.get('to_pay'))
                    payment_name = ''
                    if self._context.get('payments'):
                        payment_name = self._context.get('payments').name
                    self.env['automatic.cashback.lines'].create({
                                        'name':cashback.name,
                                        'reference': self.name + ' Success Payment ' + 'Rp.' + amount,
                                        'cashback_id': mcc_id.id,
                                        'communication' : self.name,
                                        'payment_name':payment_name,
                                        'date': self._context.get('payment_date') or fields.date.today(),
                                        'user_id': self.env.user.id,
                                        'value': total,
                                        'cashback_rule':used_rule.name,
                                        'state': 'approve',
                                        'default_posting':'debit',
                                        'cashback_rule_id': [(6, 0, [used_rule.id])],
                                    })
                    self.env['cashback.lines'].create({
                        'name':cashback.name,
                        'group_id':group_id.id,
                        'communication' : self.name,
                        'payment_name':payment_name,
                        'reference': self.name + ' Success Payment ' + 'Rp.' + amount,
                        'cashback_id': mcc_id.id,
                        'cashback_rule':used_rule.name,
                        'days': str((self._context.get('payment_date') - self.invoice_date).days) + ' ' + 'Days',
                        'date': self._context.get('payment_date') or fields.date.today(),
                        'value': total,
                        'default_posting':'debit',
                        'state': 'approve',
                        # 'cashback_rule_id': [(6, 0, line_id)],
                    })
                elif self.invoice_payment_term_id.cash_payment == True and index not in [1,0] :
                    form = self.env.ref('aos_cashback.wizard_cashback_manual_form_view')
                    context = dict(self.env.context or {})
                    context.update({'active_id':self.id,
                                    'active_model':self._name,
                                    'default_group_id':self.customer_group_id.id,
                                    'default_amount_total':self.amount_total,
                                    'default_memo':self._context.get('memo'),
                                    })
                    view = {
                        'name': "Manual Cashback",
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'cashback.manual.wizard',
                        'view_id': form.id,
                        'type': 'ir.actions.act_window',
                        'context': context,
                        'target': 'new'
                    }
                    return view
        return True
                #MISMATCH
                # elif self.invoice_payment_term_id.cash_payment == True and index != 0 :
                #     amount = 0
                #     for price in self.invoice_line_ids :
                #         amount += price.quantity * price.price_unit
                #     mismatach = self.amount_total - (amount - (data_used.formula / 100) * (amount))
                #     suppoused = self.amount_total - (amount - (data_line[0].formula / 100) * (amount))
                #     total = suppoused - mismatach
                #     if total != 0 :
                #         self.env['automatic.cashback.lines'].create({
                #                             'name':cashback.name,
                #                             'reference': self.name + ' Mismatch Payment Date ' + 'Rp.' + str(self.amount_total),
                #                             'cashback_id': mcc_id.id,
                #                             'date': self._context.get('payment_date') or fields.date.today(),
                #                             'user_id': self.env.user.id,
                #                             'communication' : self.name,
                #                             'value': total,
                #                             'cashback_rule':used_rule.name,
                #                             'state': 'approve',
                #                             'default_posting':'credit',
                #                             'cashback_rule_id': [(6, 0, [used_rule.id])],
                #                         })
                #         self.env['cashback.lines'].create({
                #             'name':cashback.name,
                #             'group_id':group_id.id,
                #             'reference': self.name + ' Mismatch Payment Date ' + 'Rp.' + str(self.amount_total),
                #             'cashback_id': mcc_id.id,
                #             'cashback_rule':used_rule.name,
                #             'communication' : self.name,
                #             'date': self._context.get('payment_date') or fields.date.today(),
                #             'value': total,
                #             'default_posting':'credit',
                #             'state': 'approve',
                #             # 'cashback_rule_id': [(6, 0, line_id)],
                #         })
    


    def js_assign_outstanding_line(self, line_id):
        res = super(AccountMove,self).js_assign_outstanding_line(line_id)
        account_payment_id = self.env['account.move.line'].browse(line_id).payment_id
        account_payment_id.reconciled_move_id = account_payment_id.reconciled_invoice_ids.ids
        self.with_context(payment_date = account_payment_id.date).cashback_pay_invoice()
        return res
    
    @api.model
    def create(self,vals):
        if self:
            for rec in self.invoice_line_ids:
                rec.cashback_percent = 0
        res = super(AccountMove,self).create(vals)
        return res

    def _compute_bool_claim(self):
        for rec in self :
            rec.bool_claim = False
            if sum(rec.invoice_line_ids.mapped('cashback_percent')) == 0 :
                rec.bool_claim = True

    @api.depends('invoice_line_ids.discount','invoice_line_ids.cashback_percent')
    def _compute_total_value(self):
        for rec in self :
            discount_total = 0
            cashback_total = rec.cashback_total
            for line in rec.invoice_line_ids:
                total = line.quantity * line.price_unit
                discount_total += total * (line.discount / 100)
                line.with_context(check_move_validity=False)._onchange_price_subtotal()
            if rec.move_type != 'entry':
                rec.with_context(check_move_validity=False)._onchange_currency()
            rec.discount_total = discount_total
            rec.discount_total_pivot = discount_total
            rec.cashback_total_pivot = cashback_total

    @api.depends('partner_id')
    def _compute_saldo_cashback(self):
        for rec in self:
            rec.saldo_cashback = 0
            if rec.customer_group_id :
                mcc_id = self.env['master.customer.cashback'].search([('group_id','=',self.customer_group_id.id),('company_id','=',self.company_id.id),('state','=','confirm')])
                rec.saldo_cashback = mcc_id.balance if mcc_id  else 0

    def button_claim_cashback(self):
        form = self.env.ref('aos_cashback.wizard_claim_cashback_form_view')
        mcc_id = self.env['master.customer.cashback'].search([('group_id','=',self.customer_group_id.id),('company_id','=',self.company_id.id),('state','=','confirm')])
        context = dict(self.env.context or {})
        context.update({'active_id':self.id,
                        'active_model':self._name,
                        'mcc_id':mcc_id.id,
                        'default_amount_total':self.amount_total,
                        'default_saldo_cashback':self.saldo_cashback,
                        })
        res = {
            'name': "Claim Cashback",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'claim.cashback.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res
    
    def button_cancel(self):
        
        for rec in self.line_ids:
            price_unit = 0
            # rec.cashback_percent = float(0)
            rec.with_context(check_move_validity=False).write({'cashback_percent':0})
            # rec.update(rec._get_price_total_and_subtotal())
            # rec.update(rec._get_fields_onchange_subtotal())
            price_unit += rec.price_unit
            rec.with_context(check_move_validity=False)._onchange_balance()
            # rec.update(rec._get_fields_onchange_balance())
            # rec.update(rec._get_fields_onchange_subtotal())
            # rec._onchange_amount_currency()
            # rec.price_unit = price_unit
            rec.with_context(check_move_validity=False).write({'price_unit':price_unit})
            rec.with_context(check_move_validity=False)._compute_amount_residual()
            rec.with_context(check_move_validity=False)._onchange_currency()
            # rec.with_context(check_move_validity=False)._onchange_price_subtotal()
            # print('xx')
        self.cashback_total = False
        res = super(AccountMove,self).button_cancel()
        # for rec in self.line_ids:
        #     rec.cashback_percent = float(0)
        #     price_unit += rec.price_unit
        #     rec.update(rec._get_fields_onchange_balance())
           
        #     rec.price_unit = price_unit
        #     rec.with_context(check_move_validity=False).update(rec._get_fields_onchange_subtotal())
        #     print('xx')
        cashback_used = False
        cashback_summary = False
        if self :
            cashback_used = self.env['cashback.used.lines'].search([('account_id','=',self.id),('state','!=','cancel')])
            cashback_summary = self.env['cashback.lines'].search([('account_id','=',self.id),('state','!=','pending')])
        if cashback_used and cashback_summary:
            cashback_used.write({'state':'cancel'})
            cashback_summary.write({'state':'pending'})
        return res
   
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cashback_percent = fields.Float(string="Cashback %")
    subtotal_internal = fields.Monetary()
    subtotal_cashback = fields.Monetary()
    internal_bool = fields.Boolean(default=False)
    product_bool = fields.Boolean(default=False)
    customer_group_id = fields.Many2one('adireksa.customer.target',related="move_id.customer_group_id")

    @api.onchange('cashback_percent','quantity', 'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())
    

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}
        # print ('===context===',self._context)
        # Compute 'price_subtotal'.
        cashback = self.cashback_percent
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        line_discount_price_unit = line_discount_price_unit * (1 - (cashback / 100.0))
        subtotal = quantity * line_discount_price_unit
    
        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(line_discount_price_unit,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
