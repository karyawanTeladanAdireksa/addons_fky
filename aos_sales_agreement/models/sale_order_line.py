from odoo import models,fields

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sale_agreement_line_id = fields.Many2one('sale.agreement.line',string="Sale Agreement Line")
    sale_agreement_id = fields.Many2one('sale.agreement',string="Sale Agreement")

class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_agreement_id = fields.Many2one('sale.agreement',string="Sale Agreement",compute="_compute_sale_agreement",store=True)

    def _compute_sale_agreement(self):
        for rec in self:
            rec.sale_agreement_id = rec.order_line.mapped('sale_agreement_id').id