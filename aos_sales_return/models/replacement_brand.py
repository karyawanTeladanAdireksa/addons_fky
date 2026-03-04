from odoo import models,fields,api,Command,_

class ReplacementBrand(models.Model):
    _name = "replacement.brand"

    return_line_id = fields.Many2one('sales.return.line',"Return Line Id")
    return_id = fields.Many2one('sales.return',string="Sales Return",related='return_line_id.return_id')
    name = fields.Char(string="Description")
    product_id = fields.Many2one('product.product',string="Product")
    brand_id = fields.Many2one('product.brand', string="Brand")
    # move_ids = fields.One2many('stock.move', string='Stock Moves')

    @api.onchange('product_id')
    def onchange_description(self):
        self.name = self.product_id.product_brand.name
    # move_ids = fields.One2many('stock.move', string='Stock Moves')

