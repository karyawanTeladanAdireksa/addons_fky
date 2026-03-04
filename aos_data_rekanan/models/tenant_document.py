from odoo import models,fields,api,_
from datetime import timedelta,date,datetime
import calendar
from calendar import monthrange
from odoo.exceptions import UserError,ValidationError

class DocumentCustomer(models.Model):
    _name = "document.customer"

    document_id = fields.Many2one('res.partner')
    name = fields.Char('Description', required=True)
    file = fields.Binary('File')
    file_name = fields.Char()
    # state = fields.Selection([('new', 'New'), ('done', 'Completed')], default='new', readonly=True,
    #                          string="Complete Document")
    is_required = fields.Boolean(string="Is Required Document",default=False)
    # Grouping Documents

    is_customers = fields.Boolean(string="Is a Customer",)
    expiry_date = fields.Date('Expiry Date' )
    notify_before = fields.Integer('Notify Before (Days)', default=10)
    tech_notify_before = fields.Integer('Notify Before (Days-For Cron)', default=10)
    state = fields.Selection([('new','New'),('running','Running'),('expired','Expired')], default='new' , readonly=True)
    boolean_doc_exp = fields.Boolean(compute="_compute_doc_expired")

    def _compute_doc_expired(self):
        for rec in self :
            rec.boolean_doc_exp = False
            if rec.expiry_date:
                if date.today() > rec.expiry_date:
                    rec.write({'state':'expired'})
                    rec.boolean_doc_exp = True

    @api.model
    def create(self, vals):
        # if vals.get('file'):
        #     vals.update({'state': 'running'})
        res = super(DocumentCustomer, self).create(vals)
        res.tech_notify_before = res.notify_before
        res.state = 'new'
        if res.file :
            res.state = 'running'
        return res

    def write(self, vals):
        if vals.get('file') or vals.get('file') == False:
            if vals.get('file'):
                vals.update({'state': 'running'})
            else:
                vals.update({'state': 'new'})
        if vals.get('notify_before') :
            self.tech_notify_before = vals.get('notify_before')
        return super(DocumentCustomer, self).write(vals)

    def unlink(self):
        return super(DocumentCustomer,self).unlink()

    def download_file(self):
        self.env.cr.execute(
            "select id from ir_attachment where res_model='" + str(self._name) + "' and res_id=" + str(self.id))
        attachment_id = self.env.cr.fetchone()[0] or None
        if attachment_id:
            attachment = self.env['ir.attachment'].sudo().browse(attachment_id)
            if attachment:
                action = {
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=ir.attachment&id=" + str(
                        attachment.id) + "&filename_field=name&field=datas&download=false&name=" + str(
                        attachment.store_fname),
                    'target': 'new'
                }
                return action
        else:
            raise UserError("Dokumen Tidak Ditemukan!!")

    def preview_file(self):
        self.env.cr.execute(
            "select id from ir_attachment where res_model='" + str(self._name) + "' and res_id=" + str(self.id))
        attachment_id = self.env.cr.fetchone()[0] or None
        if attachment_id:
            attachment = self.env['ir.attachment'].sudo().browse(attachment_id)
            if attachment:
                action = {
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=ir.attachment&id=" + str(
                        attachment.id) + "&filename_field=name&field=datas&preview=true&name=" + str(
                        attachment.store_fname),
                    'target': 'new'
                }
                return action
        else:
            raise UserError("Dokumen Tidak Ditemukan!!")
        


    @api.model
    def _send_doc_expiry_notification(self):
        self = self.sudo()
        #month = monthrange(date.day.month,date.day.year)[1]
        month = calendar.monthrange(int(datetime.today().strftime("%Y")),int(datetime.today().strftime("%m")))[1]
        tenant = self.search([('expiry_date','>=',date.today().replace(day =1)),('expiry_date','<=',date.today().replace(day =month))])
        docs = tenant.filtered(lambda x:x.expiry_date - timedelta(days=x.notify_before) == date.today())
        for document in docs :
            self.env.cr.execute(
            "select id from ir_attachment where res_model='" + str(document._name) + "' and res_id=" + str(document.id))
            attachment_id = self.env.cr.fetchone()[0] or None

            notification_date = document.expiry_date - timedelta(days=document.tech_notify_before)
            if not document.document_id.email:
                continue
            #today = date.today()
            if notification_date :
                if not document.tech_notify_before:
                    document._document_expired(attachment_id)
                else:
                    document._document_will_be_expired(document.tech_notify_before,attachment_id)
                    document.tech_notify_before -= 1
    
    def _document_expired(self,attachment_id):
        subject = "Expired Document - Request for New Document"
        mail_body = """
            <div class="page">
                <div class="container">
                    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
                        <p>
                            Dear {employee},
                        </p>
                        <p>
                            I hope this email finds you well. I am writing to inform you that we have noticed that your document(s) has expired on {exp_date}.
                            This document is a critical requirement for our records, and we request that you submit a new one as soon as possible.
                        </p>
                        <p>
                            To avoid any disruptions to your work, we kindly request you to submit the updated document at your earliest convenience. If you have already renewed your document, please send us a scanned copy of the updated one.
                        </p>
                        <p>
                            In case you have any questions or concerns, please do not hesitate to reach out to me or our HR department.
                        </p>
                        <p>
                            Best regards,
                        </p>
                        <p>
                            {company_name}
                        </p>
                        <p>
                            [Attachment: Expired Document]
                        </p>
                    </div>
                </div>
            </div>
        """.format(employee = self.document_id.name,exp_date=str(self.expiry_date),company_name=self.document_id.company_id.name)
        
        mail_id = self.env['mail.mail'].create({
            'subject':subject,
            'email_from':self.document_id.company_id.email,
            'email_to':self.document_id.email,
            'body_html':mail_body,
            'attachment_ids':[(6,0,[attachment_id])]
        })
        mail_id.sudo().send()
        self.state = 'expired'
        self.email_sent = False

    def _document_will_be_expired(self, days,attachment_id):
        subject = "Document Expiry - Request for New Document"
        mail_body = """
            <div class="page">
                <div class="container">
                    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
                        <p>
                            Dear {employee},
                        </p>
                        <p>
                            I hope this email finds you well. I am writing to inform you that we have noticed that your document(s) is about to expire on {exp_date}. This document is a critical requirement for our records, and we request that you submit a new one as soon as possible.
                        </p>
                        <p>
                            To avoid any disruptions to your work, we kindly request you to submit the updated document at your earliest convenience. Please find attached a copy of the document that is about to expire for your reference.
                        </p>
                        <p>
                            If you have already renewed your document, please send us a scanned copy of the updated one.
                        </p>
                        <p>
                            In case you have any questions or concerns, please do not hesitate to reach out to me or our HR department.
                        </p>
                        <p>
                            Best regards,
                        </p>
                        <p>
                            {company_name}
                        </p>
                        <p>
                            [Attachment: Document About to Expire]
                        </p>
                    </div>
                </div>
            </div>
        """.format(employee = self.document_id.name,exp_date=str(self.expiry_date),company_name=self.document_id.company_id.name)
        mail_id = self.env['mail.mail'].create({
            'subject':subject,
            'email_from':self.document_id.company_id.email,
            'email_to':self.document_id.email,
            'body_html':mail_body,
            'attachment_ids':[(6,0,[attachment_id])]
        })
        mail_id.sudo().send()
        #self.email_sent = True

class DocumentVendor(models.Model):
    _name = "document.vendor"

    document_id = fields.Many2one('res.partner')
    name = fields.Char('Description', required=True)
    file = fields.Binary('File')
    file_name = fields.Char()
    state = fields.Selection([('new', 'New'), ('done', 'Completed')], default='new', readonly=True,
                             string="Complete Document")
    is_required = fields.Boolean(string="Is Required Document",default=False)
    # Grouping Documents
    is_suppliers = fields.Boolean(string="Is a Supplier",)

    
    @api.model
    def create(self, vals):
        if vals.get('file'):
            vals.update({'state': 'done'})
        return super(DocumentVendor, self).create(vals)

    def write(self, vals):
        if vals.get('file') or vals.get('file') == False:
            if vals.get('file'):
                vals.update({'state': 'done'})
            else:
                vals.update({'state': 'new'})
        return super(DocumentVendor, self).write(vals)

    def unlink(self):
        return super(DocumentVendor,self).unlink()

    def download_file(self):
        self.env.cr.execute(
            "select id from ir_attachment where res_model='" + str(self._name) + "' and res_id=" + str(self.id))
        attachment_id = self.env.cr.fetchone()[0] or None
        if attachment_id:
            attachment = self.env['ir.attachment'].sudo().browse(attachment_id)
            if attachment:
                action = {
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=ir.attachment&id=" + str(
                        attachment.id) + "&filename_field=name&field=datas&download=false&name=" + str(
                        attachment.store_fname),
                    'target': 'new'
                }
                return action
        else:
            raise UserError("Dokumen Tidak Ditemukan!!")

    def preview_file(self):
        self.env.cr.execute(
            "select id from ir_attachment where res_model='" + str(self._name) + "' and res_id=" + str(self.id))
        attachment_id = self.env.cr.fetchone()[0] or None
        if attachment_id:
            attachment = self.env['ir.attachment'].sudo().browse(attachment_id)
            if attachment:
                action = {
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=ir.attachment&id=" + str(
                        attachment.id) + "&filename_field=name&field=datas&preview=true&name=" + str(
                        attachment.store_fname),
                    'target': 'new'
                }
                return action
        else:
            raise UserError("Dokumen Tidak Ditemukan!!")

class DocumentContractor(models.Model):
    _name = 'document.contractor'

class DocumentContractor(models.Model):
    _name = 'document.consultant'