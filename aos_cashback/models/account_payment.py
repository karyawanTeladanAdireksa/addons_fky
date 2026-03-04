from odoo import models,api,fields,_
from odoo.exceptions import UserError
from odoo.tools import float_compare

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        if batches[0].get('lines'):
            batches[0].update({'lines':batches[0].get('lines').sorted(key= lambda x:x.name)})
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'payment_values': {
                                **batch_result['payment_values'],
                                'payment_type': 'inbound' if line.balance > 0 else 'outbound'
                            },
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        self._post_payments(to_process, edit_mode=edit_mode)
        self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments


    def action_create_payments(self):
        payments = self._create_payments()

        if self._context.get('dont_redirect_to_payments'):
            account_id = self.env['account.move'].browse(self._context['active_ids'])
            account_ids = account_id.filtered(lambda x:x.move_type == 'out_invoice' and x.payment_state in ['paid','partial'])
            if account_ids:
                for rec in account_ids:
                    rec.with_context(payment_date=self.payment_date,memo=self.communication,payment=self,payments=payments).cashback_pay_invoice()
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        account_id = self.env['account.move'].browse(self._context['active_ids'])
        account_ids = account_id.filtered(lambda x:x.move_type == 'out_invoice'and x.payment_state in ['paid','partial'])
        if account_ids:
            for rec in account_ids:
                rec.with_context(payment_date=self.payment_date,memo=self.communication,payment=self,payments=payments).cashback_pay_invoice()
        return action

    
class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    cash_payment = fields.Boolean()
    # cashback_line_level_ids = fields.One2many('cashback.rule.line.level','payment_id')
    

class AccountPayment(models.Model):
    _inherit = "account.payment"

    reconciled_move_id = fields.Many2many('account.move')

    # def action_cancel(self):
    #     res = super(AccountPayment,self).action_cancel()
    #     if self :
    #         if self.ref :
    #             if len(self.ref.split(' ')) > 1:
    #                 for rec in self.ref.split(' '):
    #                     self.env['cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'pending'})
    #                     self.env['automatic.cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'cancel'})
    #             else:
    #                 self.env['cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'pending'})
    #                 self.env['automatic.cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'cancel'})
    #             return res 
    #         elif self.register_ids.invoice_id.filtered(lambda x:x.move_type == 'out_invoice'):
    #             for rec in self.register_ids.invoice_id.filtered(lambda x:x.move_type == 'out_invoice'):
    #                 self.env['cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'pending'})
    #                 self.env['automatic.cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'cancel'})
    #             return res 
    #         elif self.reconciled_move_id:
    #             for rec in self.reconciled_move_id.filtered(lambda x:x.move_type == 'out_invoice'):
    #                 self.env['cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'pending'})
    #                 self.env['automatic.cashback.lines'].search([('payment_name','=',self.name)]).write({'state':'cancel'})
    #             self.reconciled_move_id = False
    #             return res
    #     else :
    #         return res
        
    def action_cancel(self):
        res = super(AccountPayment,self).action_cancel()
        if self :
            if self.ref :
                if len(self.ref.split(' ')) > 1:
                    for rec in self.ref.split(' '):
                        cashback_line = self.env['cashback.lines'].search([('payment_name','=',self.name)])
                        auto_cashback = self.env['automatic.cashback.lines'].search([('payment_name','=',self.name)])
                        if cashback_line :
                            cashback_line.write({'state':'pending'})
                        if auto_cashback:
                            auto_cashback.write({'state':'cancel'})
                
                else:
                    cashback_line = self.env['cashback.lines'].search([('payment_name','=',self.name)])
                    auto_cashback = self.env['automatic.cashback.lines'].search([('payment_name','=',self.name)])
                    if cashback_line :
                        cashback_line.write({'state':'pending'})
                    if auto_cashback:
                        auto_cashback.write({'state':'cancel'})
                return res 
            elif self.register_ids.invoice_id.filtered(lambda x:x.move_type == 'out_invoice'):
                for rec in self.register_ids.invoice_id.filtered(lambda x:x.move_type == 'out_invoice'):
                    cashback_line = self.env['cashback.lines'].search([('payment_name','=',rec.name)])
                    auto_cashback = self.env['automatic.cashback.lines'].search([('payment_name','=',rec.name)])
                    if cashback_line :
                        cashback_line.write({'state':'pending'})
                    if auto_cashback:
                        auto_cashback.write({'state':'cancel'})
                return res 
            elif self.reconciled_move_id:
                for rec in self.reconciled_move_id.filtered(lambda x:x.move_type == 'out_invoice'):
                    cashback_line = self.env['cashback.lines'].search([('payment_name','=',rec.name)])
                    auto_cashback = self.env['automatic.cashback.lines'].search([('payment_name','=',rec.name)])
                    if cashback_line :
                        cashback_line.write({'state':'pending'})
                    if auto_cashback:
                        auto_cashback.write({'state':'cancel'})
                self.reconciled_move_id = False
                return res
        else :
            return res
        
        
    def action_post(self):
        super(AccountPayment,self).action_post()
        cashback = True
        for rec in self.register_ids.filtered(lambda x:x.to_reconcile):
            cashback = rec.invoice_id.with_context(payment_date = fields.date.today(),payment=self,to_pay=rec.amount_to_pay).cashback_pay_invoice()
        return cashback