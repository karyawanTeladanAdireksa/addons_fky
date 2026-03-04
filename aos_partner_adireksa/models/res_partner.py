from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError
import ast

class ResPartner(models.Model):
    _inherit = "res.partner"

    total_invoice_due = fields.Monetary(string="Total Invoice",compute="compute_total_invoice_due")
    
    def compute_total_invoice_due(self):
        self.total_invoice_due = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ]
        price_totals = self.env['account.move'].read_group(domain, ['amount_residual_signed'], ['partner_id'])
        for partner, child_ids in all_partners_and_children.items():
            partner.total_invoice_due = sum(price['amount_residual_signed'] for price in price_totals if price['partner_id'][0] in child_ids)