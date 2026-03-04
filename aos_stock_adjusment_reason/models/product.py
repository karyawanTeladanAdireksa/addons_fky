from odoo import models,_

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    
    
    def action_open_quants(self):
        action = super(ProductProduct,self).action_open_quants()
        action['view_id'] = self.env.ref('aos_stock_adjusment_reason.view_stock_quant_tree_inventory_readonly').id
        return action