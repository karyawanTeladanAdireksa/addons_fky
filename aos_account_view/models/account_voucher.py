from odoo import fields, models, api


class AccountVoucherType(models.Model):
    _inherit = 'account.voucher.type'

    company_id = fields.Many2one('res.company', string='Company')  