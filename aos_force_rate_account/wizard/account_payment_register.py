from odoo import models,fields,api
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    spot_rate = fields.Float(digits=0,string="Spot Rate")
    use_spot_rate = fields.Boolean(compute="compute_spot_rate")

    @api.depends('currency_id','journal_id')
    def compute_spot_rate(self):
        for wizard in self:
            if wizard.currency_id == wizard.env.company.currency_id:
                wizard.use_spot_rate = False
            else:
                wizard.use_spot_rate = True
            # if payment_currency != company_currency:
            #     payment.spot_rate = payment_currency._convert(1.0, company_currency, payment.company_id, payment.payment_date)
            # else:
            #     payment.spot_rate = 1.0


    def _create_payment_vals_from_wizard(self):
        if self.currency_id != self.env.company.currency_id:
            precision = self.env['decimal.precision'].precision_get('Product Price')
            if float_is_zero(self.spot_rate, precision_rounding=precision): #bug in use_spot_rate auto false if not reonchange
                raise UserError("Spot rate cannot zero")
        vals = super(AccountPaymentRegister,self)._create_payment_vals_from_wizard()
        vals.update({'force_rate':self.spot_rate})
        return vals