# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xml.etree as etr
import xml.etree.ElementTree as ET
from ast import literal_eval
import logging
_logger = logging.getLogger(__name__)

class CashbackManual(models.Model):
    _name = 'cashback.manual'
    _inherit = ["cashback.manual", "approval.matrix.mixin"]
    
    approver = fields.Text()
    approved_by_ids = fields.Many2many('res.users',compute="_compute_approver")
    minimum_approved = fields.Integer(compute="_compute_approver")
    approver_seq = fields.Integer()

    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('sent', 'RFQ Sent'),
    #     ('to approve', 'To Approve'),
    #     ('rejected', 'Rejected'),
    #     ('purchase', 'Purchase Order'),
    #     ('done', 'Locked'),
    #     ('cancel', 'Cancelled')
    # ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    
    @api.depends('approval_ids.approved_by_ids.name','approval_ids.approver_ids.name')
    def _compute_approver(self):
        for rec in self:
            approvers =""
            approved =""
            minimum_approved = 0
            approved_by_ids = rec.approval_ids.mapped('approved_by_ids')
            for line in rec.approval_ids:
                approver = line.approver_ids.mapped('name')
                minimum_approved = line.minimum_approved
                approved = ''.join(line.approved_by_ids.mapped('name'))
                approver_seq = line.approver_seq
                if approver_seq <= 1 :
                    if minimum_approved <=1 :
                        approvers = '/'.join(approver)
                    else:
                        approvers = ','.join(approver)
                    if approved != "" :
                        if approver_seq <= 1 :
                            if minimum_approved <= 1 :
                                if len(approver) == 1 :
                                    approvers = approvers.replace(approved, '')
                                else :
                                    approvers = approvers.split('/')
                                    approvers = approvers.clear()
                            else :
                                approvers = approvers.split(',')
                                approvers = ''.join(approvers)
                                approvers = approvers.replace(approved, '')
                else :
                    if minimum_approved <= 1 :
                        approver_seq -= 1
                        if approver_seq and  len(approvers) == 0 :
                            approvers += '/'.join(approver)
                        else :
                            approvers += " And "+'/'.join(approver)
                    else :
                        approver_seq -= 1
                        if approver_seq and  len(approvers) == 0 :
                            approvers += ','.join(approver)
                        else :
                            approvers += " And "+','.join(approver) 
                    if approved != ""  :
                        approver_seq += 1
                        if approver_seq > 1 :
                            if minimum_approved <= 1 :
                                if len(approver) == 1 :
                                    approvers = approvers.replace(approved, '') 
                                else :
                                    approvers = approvers.split('/')
                                    approvers = approvers.clear()
                            else :
                                approvers = approvers.split(',')
                                approvers = ''.join(approvers)
                                approvers = approvers.replace(approved, '')
            
            rec.update({
                "approver" : approvers,
                "approved_by_ids" : approved_by_ids,
                'minimum_approved':minimum_approved
            })
            

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft']:
                continue
            
            # check approval matrix
            order.sudo().checking_approval_matrix(require_approver=True)
            
            # if here not raises anything on approval matrix than it true / rules was passed
            # if any rules then it will registered on rule_ids
            # if not any rules,then probably it not required approvers
            if not order.approval_ids:
                order.action_confirm()  
                # original: add supplier into product
                return True
            else:
                order.write({'state': 'waiting'})
            # if has any rules then write state into "to approve"
    
    def btn_approve(self):
        if not self._context.get('force_request'):    
            self.approving_matrix()
        if self.approved:     
            self.with_context(allowed_company_ids=self.company_id.ids,cids=self.company_id.id).action_confirm()

    # def _prepare_report(self,res):
    #     get_model = self.sudo().env['ir.model'].search([('model','=',res._name)])
    #     get_report_id = self.sudo().env['jasper.report'].search([('model_id','=',get_model.id)])
    #     context = dict(res._context)
    #     context.update({
    #         'active_id':res.id,
    #         'active_ids':res.ids,
    #         'active_model':res._name,
    #         'docid':res.id,
    #         'docids':res.ids,
    #         'print_not_from_ui':True
    #     })
    #     return (get_report_id,context)

    # def print_quotation(self):
    #     self.write({'state': "sent"})
    #     result = self._prepare_report(self)
    #     return result[0].with_context(result[1]).run_report(self.ids)

    # def action_rfq_send(self):
    #     """ Override Method Rfq send """
    #     '''
    #     This function opens a window to compose an email, with the edi purchase template message loaded by default
    #     '''
    #     self.ensure_one()
    #     result = self._prepare_report(self)
    #     result[0].with_context(result[1]).run_report(self.ids)

    #     ir_model_data = self.env['ir.model.data']
    #     # attachment = self.sudo().env['ir.attachment'].search([('res_id','=',self.id),('res_model','=',self._name)])
    #     try:
    #         if self.env.context.get('send_rfq', False):
    #             template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
    #         else:
    #             template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase_done')[2]
    #     except ValueError:
    #         template_id = False
    #     try:
    #         compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
    #     except ValueError:
    #         compose_form_id = False
    #     ctx = dict(self.env.context or {})
    #     ctx.update({
    #         'default_model': 'purchase.order',
    #         'active_model': 'purchase.order',
    #         'active_id': self.ids[0],
    #         'default_res_id': self.ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         # 'default_attachment_ids':[(4,attachment.id)],
    #         'default_composition_mode': 'comment',
    #         'custom_layout': "mail.mail_notification_paynow",
    #         'force_email': True,
    #         'mark_rfq_as_sent': True,
    #     })

    #     # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
    #     # object. Therefore, we pass the model description in the context, in the language in which
    #     # the template is rendered.
    #     lang = self.env.context.get('lang')
    #     if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
    #         template = self.env['mail.template'].browse(ctx['default_template_id'])
    #         if template and template.lang:
    #             lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

    #     self = self.with_context(lang=lang)
    #     if self.state in ['draft', 'sent']:
    #         ctx['model_description'] = _('Request for Quotation')
    #     else:
    #         ctx['model_description'] = _('Purchase Order')

    #     return {
    #         'name': _('Compose Email'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(compose_form_id, 'form')],
    #         'view_id': compose_form_id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def button_reject(self):
        self.state = 'cancel'
        self.rejecting_matrix()
        # self.button_cancel()
        
    def open_reject_message_wizard(self):
        self.ensure_one()
        
        form = self.env.ref('approval_matrix.message_post_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'default_prefix_message':"<h4>Rejecting CashBack Manual</h4>","default_suffix_action": "button_reject"}) #uncomment if need append context
        context.update({'active_id':self.id,'active_ids':self.ids,'active_model':'cashback.manual'})
        res = {
            'name': "%s - %s" % (_('Rejecting Cashback Manual'), self.name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'message.post.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

#     def __authorized_form(self, root):
#           
#         def append_readonly_non_draft(elm):
#             # _logger.info(('---- loop', elm.tag))
#             if elm.tag!='field':
#                 return elm
#             
#             # _logger.info(('-------------->', elm.get('name')))
#             attrs = elm.get('attrs')
#             
#             if attrs:
#                 # IF HAS EXISTING "attrs" ATTRIBUTE
#                 attrs_dict = literal_eval(attrs)
#                 attrs_readonly = attrs_dict.get('readonly')
#                 # if had existing readonly rules on attrs will append it with or operator
#                 
#                 if attrs_readonly:
#                     if type(attrs_readonly) == list:
#                         # readonly if limit_approval_state not in draft,approved
#                         # incase:
#                         # when so.state locked (if limit automatically approved the limit_approval_state will still in draft) so will use original functions
#                         # when so.state == draft and limit approval strate in (need_approval_request,  need_approval, reject) will lock the field form to readonly
#                         
#                         # print(attrs_readonly)
#                         # forced domain
#                         attrs_readonly = [('state', 'not in',['draft'])]
#                     attrs_dict.update({'readonly':attrs_readonly})
#                 else:
#                     # if not exsit append new readonly key on attrs
#                     attrs_dict.update({'readonly':[('state','not in',['draft'])]})
#             else:
#                 
#                 attrs_dict = {'readonly':[('state','not in',['draft'])]}
#             try:
#                 new_attrs_str = str(attrs_dict)
#                 elm.set('attrs',new_attrs_str)
#             except Exception as e:
#                 pass
# 
#             return elm
# 
# 
#         def set_readonly_on_fields(elms):
#             for elm in elms:
# 
#                 if elm.tag=='field':
#                     elm = append_readonly_non_draft(elm)
#                 else:
#                     if len(elm)>0:
#                         _logger.info((len(elm)))
#                         if elm.tag in ['tree','kanban','form','calendar']:
#                             continue # skip if *2many field child element
#                         elm = set_readonly_on_fields(elm)
#                     else:
#                         if elm.tag=='field':
#                             elm = append_readonly_non_draft(elm)
#             return elms
#         paths = []
#         for child in root:
#             if child.tag=='sheet':
#                 # child = append_readonly_non_draft(child)
#                 child = set_readonly_on_fields(child)
#         return root
# 
#     @api.model
#     def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
# 
#         sup = super()._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
#         # get generated xml view
#         
#         # if form
#         if view_type=='form':
#             root_elm = ET.fromstring("%s" % (sup['arch']))
#             # AUTHORIZED ALL "<field>" element
#             new_view = self.__authorized_form(root_elm)
#             sup.update({'arch':ET.tostring(new_view)})
# 
#         return sup