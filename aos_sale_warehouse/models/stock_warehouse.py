# -*- coding: utf-8 -*-

from odoo import api, models,fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_pack = fields.Boolean(string="Is Package Required ?")


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    packaging_id = fields.Many2one('product.packaging',string="Packaging")
    qty_pack = fields.Integer(string="Qty Packaging")