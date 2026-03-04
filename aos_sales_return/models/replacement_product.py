from odoo import models,fields,api


class ReplacementProduct(models.Model):
    _name = "replacement.product"

    return_line_id = fields.Many2one('sales.return.line',"Return Line Id")
    return_id = fields.Many2one('sales.return',string="Sales Return",related='return_line_id.return_id')
    name = fields.Char(string="Description")
    product_id = fields.Many2one('product.product',string="Product")
    brand_id = fields.Many2one('product.brand', string="Brand")
    qty = fields.Float(string="Qty")
    price_unit = fields.Float(string="Price Unit", readonly=True)
    price_subtotal = fields.Float(string="Price Subtotal",compute="_compute_price_subtotal",store=True)
    # move_ids = fields.One2many('stock.move', string='Stock Moves')

    @api.onchange('product_id')
    def onchange_description(self):
        self.name = self.product_id.display_name
        self.brand_id = self.product_id.product_brand.id 

    @api.depends('price_unit','qty')
    def _compute_price_subtotal(self): 
        for line in self:
            line.price_subtotal = line.price_unit * line.qty