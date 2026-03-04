from odoo import models,fields,api

class AccountMove(models.Model):
    _inherit = "account.move"

    user_can_edit = fields.Boolean(string="Can Edit",help="**If true can edit\n**If false cant edit Quantity, Price Unit, Discount",compute="_compute_user_can_edit")

    # @api.model
    # def default_get(self,fields_list):
    #     res = super(AccountMove,self).default_get(fields_list)
    #     if self._context.get('default_move_type') == 'out_invoice' or ('move_type' in res and res['move_type'] == 'out_invoice'):
    #         if self.env.user.has_group('invoice_line_security.allow_to_update_invoice_line'):
    #             res['user_can_edit'] = True
    #         else:
    #             res['user_can_edit'] = False
    #     else:
    #         res['user_can_edit'] = True
    #     return res
    
    def _compute_user_can_edit(self):
        for move in self:
            if not self.env.user.has_group('invoice_line_security.allow_to_update_invoice_line') and move.move_type == 'out_invoice':
                move.user_can_edit = False
            else:
                move.user_can_edit = True