from odoo import models,fields,api,_
from odoo.exceptions import UserError,ValidationError

class DocumentList(models.Model):
    _name = "document.type"
    _description = "Document Type"

    name = fields.Char(string="Document Name")
    
class DocumentTemplate(models.Model):
    _name = "document.template"
    _description = "Document Template"

    name = fields.Char(string="Template Name",required=True)
    template_ids = fields.One2many('document.template.line','doc_id',string="Template Line")
    tenant_type = fields.Selection([
        ('customer','Customer'),
        ('supplier','Supplier'),
    ],string="Contact Type",required=True,default="customer")

class DocumentTemplateLine(models.Model):
    _name = "document.template.line"
    _description = "Document Template Line"
    
    doc_id = fields.Many2one("document.template")
    document_type = fields.Many2one("document.type",string="Document Type")
    is_required = fields.Boolean(string="Is Required Document",default=False)