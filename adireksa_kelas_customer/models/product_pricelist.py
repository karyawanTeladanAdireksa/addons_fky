from odoo import models, fields

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    kelas = fields.Selection(
        [('blue', 'Blue (Annapurna)'),
         ('platinum', 'Platinum'),
         ('gold', 'Gold'),
         ('silver', 'Silver'),
         ('kelas_1_2', 'Kelas 2 & Kelas 1')],
        string='Kelas'
    )
    kelas_id = fields.Many2one(
        'customer.class',
        string='Kelas',
    )