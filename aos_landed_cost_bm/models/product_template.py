# from random import randint
from odoo import models,api,fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bea_masuk = fields.Integer(string="Bea Masuk")
    landed_account = fields.Many2one('account.account',string="Landed Cost Account")
    split_method_landed_cost = fields.Selection(
                        selection_add=[
                            ("by_bm", "By Bea Masuk"),
                        ],
                        ondelete={"by_bm": "cascade"},
                        )