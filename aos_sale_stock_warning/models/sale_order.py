from odoo import models,api,_
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_cancel(self):
        for order in self:
            for move in order.order_line.mapped('move_ids'):
                if move.state == 'done':
                    raise UserError(_('Unable to cancel sales order %s as some delivery have already been done.') % (order.name))
                
        return super(SaleOrder,self).action_cancel()