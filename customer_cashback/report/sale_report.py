# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    state_id = fields.Many2one('res.country.state', string='Partner State', readonly=True)
    before_tax_total = fields.Float(
        string='Total Untaxed',
    )
    def _select(self):
        query = '''
        ,
          (
            s.amount_untaxed - s.discount_amount - (
              s.amount_untaxed - s.discount_amount + s.amount_tax
            )* COALESCE(s.cashback_per, 0.0) / 100.0
          )/(
            SELECT
            -- what if count is zero? will it be prompting error division by zero?
              count(*)
            FROM
              sale_order_line sl
            WHERE
              sl.order_id = s.id
          ) AS before_tax_total
        '''
        return super(SaleReport, self)._select() + query

    def _group_by(self):
        grouby = '''
        ,
          s.amount_untaxed,
          s.cashback_per,
          s.amount_tax,
          s.discount_amount,
          s.id
        '''
        return super(SaleReport, self)._group_by() + grouby

