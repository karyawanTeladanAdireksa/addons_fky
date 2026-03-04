from odoo import api, fields, models, _

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    group_class_id = fields.Many2one('cashback.class.group',string="Group Class")