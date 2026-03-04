from odoo import api, fields, models, _

class CashbackClassGroup(models.Model):
    _name = 'cashback.class.group'
    _inherit = ['mail.thread']
    _description = 'Cashback Class Group'

    name = fields.Char(string="Name", required=False, )
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.user.company_id.id)