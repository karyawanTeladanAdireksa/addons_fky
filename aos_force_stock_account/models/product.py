# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _svl_empty_stock_am(self, stock_valuation_layers):
        move_vals_list = super(ProductProduct, self)._svl_empty_stock_am(stock_valuation_layers=stock_valuation_layers)
        #print ('--SEBELUM==DEBIT---',move_vals_list[0]['line_ids'][0][2])
        #print ('--CREDIT---',move_vals_list[0]['line_ids'][1][2])
        if move_vals_list:
            product = self.browse(move_vals_list[0]['line_ids'][0][2]['product_id'])
            product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in stock_valuation_layers.mapped('product_id')}
            #JIKA GANTI CATEGORY ATAU STOCK VALUATION (UTK RECONCILE ANTARA AKUN INPUT SAJA)
            debit_account_id = product_accounts[product.id]['stock_input'].id
            #UPDATE ACCOUNT YG DI DEBIT
            move_vals_list[0]['line_ids'][0][2].update({'account_id': debit_account_id})
            #print ('--SESUDAH==DEBIT---',move_vals_list[0]['line_ids'][0][2])
        return move_vals_list
            