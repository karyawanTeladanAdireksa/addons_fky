from odoo import api, fields, models, _

class CashbackInvoice(models.Model):
    _name = 'cashback.invoice'
    _description = 'Cashback Invoice'

    name = fields.Char(string="Name")
    invoice_ids = fields.Many2many('account.move')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.user.company_id.id)

