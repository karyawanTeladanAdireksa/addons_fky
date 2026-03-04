# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
import logging
_logger = logging.getLogger(__name__)



class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _available_credit(self):
        for res in self:
            sale_orders = self.env['sale.order'].search([('partner_id','=',res.id),('state','=','sale')])
            amount = 0.0
            for sale in sale_orders:
                amount += sale.amount_total
            _logger.error("\n\n=======Res Id ------------------------------------------------->%s", res.id)
            _logger.error("\n\n=======Amount ------------------------------------------------->%s", amount)
            _logger.error("\n\n=======credit_limit ------------------------------------------------->%s", res.credit_limit)
            value = 0.0
            if res.credit_limit:
                value = res.credit_limit - amount
            _logger.error("\n\n=======Value ------------------------------------------------->%s", value)
            res.available_credit = value
            _logger.error("\n\n=======Available Credit ------------------------------------------------->%s", res.available_credit)
            _logger.error("\n\n\n\n")

    over_credit = fields.Boolean('Allow Over Credit?')
    available_credit = fields.Float('Available Credit')

