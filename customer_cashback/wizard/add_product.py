# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AddProductLines(models.TransientModel):

    _name = 'add.product.lines'
    _description = 'Add Product Lines'

    @api.model
    def _get_cashback_product_id(self):
        cashback_product_id = self.env.context.get('active_id', False)
        return cashback_product_id

    @api.model
    def _get_categ_ids(self):
        active_id = self.env.context.get('active_id', False)
        cashback_product_id = self.env['master.cashback.product'].browse(active_id)
        return cashback_product_id.product_categ_ids

    product_ids = fields.Many2many('product.product', string="Products")
    cashback_product_id = fields.Many2one('master.cashback.product', default=_get_cashback_product_id)
    categ_ids = fields.Many2many('product.category', default=_get_categ_ids, string="Categories")

    def add_product(self):
        for rec in self.product_ids:
            self.env['cashback.product.lines'].create({
                         'product_id': rec.id,
                         'cashback_id': self.cashback_product_id.id
                         })
        return True
