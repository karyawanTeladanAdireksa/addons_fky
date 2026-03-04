from odoo import models,fields,_


class SalesReturnApproval(models.Model):
    _name = "sales.return"
    _inherit = ['sales.return','approval.matrix.mixin']
    
    state = fields.Selection(selection_add=[('waiting_approval','Waiting Approval'),('confirm',),('cancel',),('reject','Reject')], ondelete={'waiting':'set null','reject':'set null'})
    
    def action_approval(self):
        self._validate_replacement_line()
        self.sudo().checking_approval_matrix(require_approver=False)
        if not self.approval_ids:
            return self.action_confirm()
        
        self.state = 'waiting_approval'
        
    def action_approve(self):
        if not self._context.get('force_request'):
            self.approving_matrix()
            
        if self.approved:
            self.action_confirm()
    
    def action_reject(self):
        self.state = 'reject'
        
    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Sales Return</h4>","default_suffix_action": "action_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':self._name})
        res = {
            'name': "%s - %s" % (_('Rejecting Sales Return'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res