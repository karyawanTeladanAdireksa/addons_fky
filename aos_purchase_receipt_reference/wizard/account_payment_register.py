from odoo import models,api

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"
    
    
    @api.model
    def default_get(self, fields):
        res = super(AccountPaymentRegister,self).default_get(fields)
        moves = self.env[self._context.get('active_model','account.move')].browse(self._context.get('active_ids'))
        if 'communication' in res and len(moves) == 1:
            res['communication'] = res['communication'] + " - " + moves.ref if moves.ref else ""
        return res