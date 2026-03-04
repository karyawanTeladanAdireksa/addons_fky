from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cashback_id = fields.Many2many('adireksa.cashback', string="Cashback")

    def _prepare_invoice(self):
        res = super(SaleOrder,self)._prepare_invoice()
        res.update({
            # 'diskon': [(6, 0, self.diskon.ids)],
            # 'kelas_customer': self.kelas_customer,
            'cashback_id': self.cashback_id,
        })
        # if self.diskon:
        #     res.update({'diskon_bool': True})
        if self.cashback_id:
            res.update({'cashback_bool': True})
        return res
