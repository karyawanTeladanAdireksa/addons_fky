from odoo import models,fields,api,_
from odoo.exceptions import ValidationError
from datetime import datetime

class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner","approval.matrix.mixin"]

    state = fields.Selection([('draft','Draft'),('waiting','Waiting Approval'),('approve','Approved'),('reject','Not Approved')], default='draft')
    # Override field company id
    # tujuan:
    # sekarang field company_id di approval matrix itu required
    # field company_id di res_partner tidak default
    company_id = fields.Many2one('res.company', 'Company', index=True,default=lambda self:self.env.company.id)

    def draft_wating(self):
        for line in self:
            line.sudo().checking_approval_matrix(require_approver=False)
            child = line.child_ids.filtered(lambda x:x.state == 'draft')
            # if here not raises anything on approval matrix than it true / rules was passed
            # if any rules then it will registered on rule_ids
            # if not any rules,then probably it not required approvers
            if not line.approval_ids:
                line.action_approved()
                if child:
                    child.action_approved()
                return True
            if child:
                for rec in child:
                    rec.write({'state':'waiting'})
            line.write({'state':'waiting'})
            
    def button_approve(self):
        child = self.child_ids.filtered(lambda x:x.state == 'waiting')
        if not self._context.get('force_request'):    
            self.approving_matrix()
            if child:
                for ch in child:
                    ch.approving_matrix()
        if self.approved:
            if child:
                child.with_context(allowed_company_ids=self.company_id.ids,cids=self.company_id.id).action_approved()
            self.with_context(allowed_company_ids=self.company_id.ids,cids=self.company_id.id).action_approved()
    
    def button_reject(self):
        self.write({'state': 'reject'})

    def action_approved(self):
        for line in self:
            line.write({'state':'approve'})

    def action_cancel(self):
        self.write({'state':'cancel'})

    def set_to_draft(self):
        self.write({'state':'draft'})

    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting Tenant</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':self._name})
        res = {
            'name': "%s - %s" % (_('Rejecting Tenant'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def unlink(self):
        for rec in self :
            if rec.state != 'draft':
                raise UserError(_(" Hanya Boleh DiDelete Pada Saat Draft "))
            return super(ResPartner , self).unlink()

    def write(self,vals):
        if self.env.user.email == False:
                self.env.user.email = self.env.user.login
        # if self.state != 'draft':
        #     if not vals.get('state'):
        #         raise UserError(_(" Hanya Boleh Diubah Saat State Draft "))
        # if vals.get('state'):
        #     time = datetime.now()
        #     under = "Waiting Approval"
        #     body_log = "Contact %s Change State From %s To %s At %s" % (self.name , self.state , under if vals.get('state') == 'waiting' else vals.get('state') , str(time.strftime("%Y-%m-%d")))
        #     self.message_post(body = body_log)
        return super(ResPartner , self).write(vals)