from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        if self.cashback_id:
            for sale in self.env['sale.order'].browse(self._context.get('active_ids', [])):
                record = self.env['customer.cashback'].create({
                    'partner_id': sale.partner_id.id,
                    'group_id': [(6, 0, sale.partner_id.category_id.ids)],
                    'nilai_cashback': self.cashback_id.cashback_formula,
                })
                record.action_approve()
        return res
