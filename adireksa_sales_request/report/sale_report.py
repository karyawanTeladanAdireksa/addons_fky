# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    state_id = fields.Many2one('res.country.state', string='Partner State', readonly=True)

    def _select(self):
        return super(SaleReport, self)._select() + ", partner.state_id as state_id"
 
    def _group_by(self):
        return super(SaleReport, self)._group_by() + ", partner.state_id"

