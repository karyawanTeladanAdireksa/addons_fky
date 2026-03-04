from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_unit = fields.Monetary('Unit Price', required=True, digits='Product Price', default=0.0)