# -*- coding: utf-8 -*-

from odoo import api, models,fields,_
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    qty_pack = fields.Integer(string="Qty Packaging")


    @api.onchange('qty_pack','product_packaging_id')
    def _onchange_qty_product(self):
        self.product_uom_qty = self.qty_pack * self.product_packaging_id.qty

    