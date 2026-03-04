# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _available_credit(self):
        for res in self:
            sale_orders = self.env['sale.order'].search([('partner_id','=',res.id),('state','=','sale'),('invoice_status','=','invoiced')])
            amount = 0.0
            for sale in sale_orders:
                amount += sale.amount_total
            value = 0.0
            if res.credit_limit and amount:
                 value = res.credit_limit - amount
            res.available_credit = value

    over_credit = fields.Boolean('Allow Over Credit?')
    available_credit = fields.Float('Available Credit',readonly=True,compute='_available_credit')

