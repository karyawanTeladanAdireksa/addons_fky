# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    # @api.model
    # def _update_last_login(self):
    #     cr = self.env.cr
    #     res = super(ResUsers, self)._update_last_login()
    #     cr.execute("""update account_context_general_ledger set date_from = date_trunc('month', current_date) where date_from is null""")
    #     cr.execute("""update account_context_general_ledger set date_to = date_trunc('month', now()) + interval '1 month -1 day'+ now()::time where date_to is null""")
    #     cr.execute("""update account_context_general_ledger set date_filter='custom'""")
    #     return res
