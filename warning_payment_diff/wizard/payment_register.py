from odoo import models,api
from odoo.exceptions import UserError
from odoo.tools import float_compare

class PaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        precision = self.env['decimal.precision'].precision_get('Product Price')
        if self.payment_difference_handling == 'reconcile':
            if float_compare(self.payment_difference, 50_000.00,precision_digits=precision) > 0:
                raise UserError("Payment Different can`t more than 50,000.00")
        return super(PaymentRegister,self).action_create_payments()
    
    @api.onchange('amount')
    def onchange_amount_to_pay(self):
        if self.group_payment:
            self.register_ids.amount_to_pay = self.amount