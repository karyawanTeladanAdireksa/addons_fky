from odoo import models
from ast import literal_eval

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"
    
    
    #Override
    def _get_action(self, action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        if self:
            action['display_name'] = self.display_name

        default_immediate_tranfer = False
        # if self.env['ir.config_parameter'].sudo().get_param('stock.no_default_immediate_tranfer'):
        #     default_immediate_tranfer = False

        context = {
            'search_default_picking_type_id': [self.id],
            'default_picking_type_id': self.id,
            'default_immediate_transfer': default_immediate_tranfer,
            'default_company_id': self.company_id.id,
        }

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action