from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_payment_name(self):
        if self.payment_term_id:
                number = [int(s) for s in self.payment_term_id.name.split() if s.isdigit()]
                if number:
                    self.payment_day = number[0]

    payment_day = fields.Char(compute='_get_payment_name', string='Payment note', help="only for report field payment term")

class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_acc_invoice = fields.Text(
        string='Bank Account Footer Invoice',
    )
