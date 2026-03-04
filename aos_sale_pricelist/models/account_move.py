from odoo import api, fields,models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    pricelist_ids = fields.Many2one('product.pricelist', string='Pricelist')

    @api.model
    def create(self,vals):

        res = super(AccountMove,self).create(vals)
        if res.pricelist_id or res.pricelist_ids:
            maximum_discount = res.invoice_line_ids.filtered(lambda x:x.discount > res.pricelist_id.max_discount) if res.pricelist_id else res.invoice_line_ids.filtered(lambda x:x.discount > res.pricelist_ids.max_discount)
            if maximum_discount:
                raise UserError(_(f'Discount Maximum Is {res.pricelist_id.max_discount if res.pricelist_id else res.pricelist_ids.max_discount } %' ))
        return res
    
    def write(self,vals):
        res = super(AccountMove,self).write(vals)
        if self.pricelist_id and len(self) == 1:
            maximum_discount = self.invoice_line_ids.filtered(lambda x:x.discount > self.pricelist_id.max_discount) if self.pricelist_id else self.invoice_line_ids.filtered(lambda x:x.discount > self.pricelist_ids.max_discount)
            if maximum_discount:
                raise UserError(_(f'Discount Maximum Is {self.pricelist_id.max_discount if self.pricelist_id else self.pricelist_ids.max_discount} %' ))
        return res