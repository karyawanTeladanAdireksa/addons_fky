from odoo import models,api,fields,_
from odoo.exceptions import UserError
from odoo.tools import float_compare

class StockPicking(models.Model):
    _inherit = "stock.picking"

    area_id = fields.Many2one("customer.area", related="partner_id.group_id.area_id")
    customer_group_id = fields.Many2one("adireksa.customer.target", string="Customer Group", related="partner_id.group_id")

    picking_type_name = fields.Char(related="picking_type_id.name")