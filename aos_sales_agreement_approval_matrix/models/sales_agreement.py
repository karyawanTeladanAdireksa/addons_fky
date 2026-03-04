from odoo import models,fields,api,_

class SaleAgreement(models.Model):
    _name = "sale.agreement"
    _inherit = ["sale.agreement","approval.matrix.mixin"]

    state = fields.Selection([('draft','Draft'),
                              ('waiting_approval','Waiting Approval'),
                              ('running','Running'),
                              ('done','Locked'),
                              ('unlocked','Unlocked'),
                              ('rejected','Rejected'),
                              ('cancel','Cancelled')],
                              string="State",default="draft",tracking=1)

    def action_approval(self):
        self.sudo().checking_approval_matrix(require_approver=True)
        if not self.approval_ids:
            self.action_confirm()
        
        self.state = 'waiting_approval'

    def action_approve(self):
        if not self._context.get('force_request'):    
            self.approving_matrix()

        if self.approved:
            self.action_confirm()

    
    def action_reject(self):
        self.state = 'rejected'

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Sales Agreement</h4>","default_suffix_action": "action_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':self._name})
        res = {
            'name': "%s - %s" % (_('Rejecting Sales Agreement'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res