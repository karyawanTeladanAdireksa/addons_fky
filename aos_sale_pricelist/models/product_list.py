from odoo import api, fields,models, _
from odoo.exceptions import UserError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    max_discount = fields.Float(string="Maximum Discount",required=True)


    @api.model
    def create(self,vals):

        res = super(ProductPricelist,self).create(vals)
        for rec in res.item_ids:
            if rec.compute_price == 'percentage':
                if rec.percent_price > res.max_discount:
                    raise UserError(_(f'Discount Maximum Is {res.max_discount} %' ))
        return res
    
    def write(self,vals):
        res = super(ProductPricelist,self).write(vals)
        for rec in self.item_ids:
            if rec.compute_price == 'percentage':
                if rec.percent_price > self.max_discount:
                    raise UserError(_(f'Discount Maximum Is {self.max_discount} %' ))
        return res