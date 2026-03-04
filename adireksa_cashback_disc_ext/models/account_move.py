from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        self.kelas_customer = p.kelas
        return res
