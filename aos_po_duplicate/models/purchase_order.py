from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError
import ast

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def purchase_line_duplicate(self,vals):
        duplicate_item = []
        if vals:
            for rec in vals:
                if rec[2] != False and rec[0] == 0:
                    product_id = self.env['product.product'].browse(rec[2].get('product_id'))
                    if self :
                        if product_id.id in self.order_line.mapped('product_id').ids:
                            raise UserError(_('%s is Duplicate') % product_id.display_name )
                    if self._context.get('po'):
                        if product_id.id not in duplicate_item  :
                            duplicate_item.append(product_id.id)
                            continue
                        else:
                            raise UserError(_('%s is Duplicate') % product_id.display_name )
    @api.model
    def create(self,vals):
        res = super(PurchaseOrder,self).create(vals)
        self.with_context(po=res.id).purchase_line_duplicate(vals.get('order_line',False))
        return res
    
    def write(self,vals):
        if vals.get('order_line'):
            self.purchase_line_duplicate(vals.get('order_line',False))
        res = super(PurchaseOrder,self).write(vals)
        return res