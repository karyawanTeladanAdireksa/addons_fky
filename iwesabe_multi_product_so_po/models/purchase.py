from odoo import fields, models,api,_


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    # OVERRIDE
    name = fields.Text(string='Description', required=False)