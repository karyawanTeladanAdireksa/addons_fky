from odoo import models,fields,api


class SalesReturn(models.Model):
    _inherit = "sales.return"
    
    force_account_id = fields.Many2one('account.account',string="Force Account")
    
    
    def _get_prepare_picking(self):
        res = super(SalesReturn,self)._get_prepare_picking()
        res.update({'account_force_id':self.force_account_id.id})
        return res