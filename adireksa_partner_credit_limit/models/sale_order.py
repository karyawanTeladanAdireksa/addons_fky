# -*- coding: utf-8 -*-
from odoo import api, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def check_limit(self):
        partner = self.partner_id
        account_invoices = self.env['account.invoice'].search([('partner_id','=',partner.id),('state','not in',['draft','cancel'])])
        residual = 0.0
        for invoice in account_invoices:
            residual += invoice.residual
        check_amount = residual + self.amount_total
        if check_amount > partner.credit_limit:
            up_limit = "Rp. {:,.0f}".format(check_amount - partner.credit_limit)
            if not partner.over_credit:
                msg = """Nilai penjualan melebihi batas kredit customer!
                        Perlu approval kenaikan limit sebesar %s.""" %(up_limit)
                raise UserError(_('Credit Over Limits !\n' + msg))
            else:
                return True
        else:
            return True
