# -*- coding: utf-8 -*-
from odoo import fields, models,api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # def _available_credit(self):
    #     # Override function. The original code cannot be used on Adireksa business process 
    #     for res in self:
    #         account_invoices = self.env['account.invoice'].search([('partner_id','=',res.id),('state','not in',['draft','cancel'])])
    #         amount = 0.0
    #         for invoice in account_invoices:
    #             amount += invoice.residual
    #         value = 0.0
    #         if res.credit_limit and amount:
    #              value = res.credit_limit - amount
    #         res.available_credit = value