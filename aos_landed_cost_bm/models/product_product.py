# from random import randint
from odoo import models,api,fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    bea_masuk = fields.Integer(string="Bea Masuk",related="product_tmpl_id.bea_masuk")
    landed_account = fields.Many2one('account.account',string="Landed Cost Account",related="product_tmpl_id.landed_account")
