from odoo import models,fields

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    
    def _prepare_picking(self):
        res = super(PurchaseOrder,self)._prepare_picking()
        res['partner_ref'] = self.partner_ref
        return res