from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError
import ast

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    parent_id = fields.Many2one('purchase.order')
    back_bool = fields.Boolean()

    def action_open_po_back_order(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "views": [[False, "form"]],
            "res_id": self.parent_id.id,
        }
    
    def create_po_backorder(self):
        form = self.sudo().env.ref(
            'aos_po_backorder.backorder_wizard_form', raise_if_not_found=False)
        return {
            'name': _('Create PO Backorder'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'backorder.wizard',
            'views': [(form.id, 'form')],
            'view_id': form.id,
            'target': 'new',
            'context': {},
        }