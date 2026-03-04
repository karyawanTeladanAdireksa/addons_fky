from odoo import api, fields,models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cashback_id = fields.Integer()

    @api.model
    def create(self,vals):

        res = super(SaleOrder,self).create(vals)
        if res.pricelist_id:
            for rec in res.order_line:
                if rec.discount > res.pricelist_id.max_discount:
                        raise UserError(_(f'Discount Maximum Is {res.pricelist_id.max_discount} %' ))
        return res
    
    def write(self,vals):
        res = super(SaleOrder,self).write(vals)
        if self.pricelist_id:
            maximum_discount = self.order_line.filtered(lambda x:x.discount > self.pricelist_id.max_discount)
            if maximum_discount:
                raise UserError(_(f'Discount Maximum Is {self.pricelist_id.max_discount} %' ))
        return res
    
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        sale_obj = self.env['sale.order'].browse(self._context.get('active_id'))
        if res.get('res_id') != 0:
            account_obj = self.env['account.move'].browse(res.get('res_id'))
            for rec in account_obj:
                 rec.pricelist_id = sale_obj.pricelist_id.id
            return res
        elif res.get('domain'):
            account_obj = self.env['account.move'].browse(res.get('domain')[0][2])
            for rec in account_obj:
                 rec.pricelist_id = sale_obj.pricelist_id.id
            return res
    
            