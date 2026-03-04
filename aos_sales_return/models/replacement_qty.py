from odoo import models,fields,api,Command,_

class ReplacementQty(models.Model):
    _name = "replacement.qty"

    return_line_id = fields.Many2one('sales.return.line',"Return Line Id")
    return_id = fields.Many2one('sales.return',string="Sales Return",related='return_line_id.return_id')
    name = fields.Char(string="Description")
    product_id = fields.Many2one('product.product',string="Product")
    qty = fields.Float(string="Qty",required=False,default=1) 

    
    @api.onchange('return_line_id')
    def onchange_description(self):
        self.name = self.return_line_id.qty 