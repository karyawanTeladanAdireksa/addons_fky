from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_request_id = fields.Many2one('sale.request', string='Sale Request Reference')
