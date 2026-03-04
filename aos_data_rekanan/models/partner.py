from odoo import models, fields, api ,_
from odoo.exceptions import UserError
from datetime import datetime

class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.model
    def default_get_customer(self):
        if self._context.get('res_partner_search_mode') :
            if self._context.get('res_partner_search_mode') == 'supplier' :
                return False
            else :
                return True
        else:
            return True
        # res = super(ResPartner,self).default_get_customer(fields)
        # if 'type' in res and res['type'] == 'delivery':
        #     res['is_customers'] = True
        # return res
    @api.model
    def default_get_supplier(self):
        if self._context.get('res_partner_search_mode') :
            if self._context.get('res_partner_search_mode') == 'supplier' :
                return True
        else:
            return False
        
    # @api.model
    # def default_get_bool(self,fields):
    #     if self._context.get('res_partner_search_mode') :
    #         if self._context.get('res_partner_search_mode') == 'supplier' :
    #             return True
    #     else:
    #         return False

    state = fields.Selection([('draft','Draft'),('waiting','Waiting Approval'),('approve','Approved'),('reject','Not Approved')], default='draft')
    is_customers = fields.Boolean(string="Is a Customer", default=default_get_customer)
    is_suppliers = fields.Boolean(string="Is a Supplier", default=default_get_supplier)

    tempat_lahir = fields.Char(string="Tempat Lahir")
    tanggal_lahir = fields.Date(string="Tanggal Lahir")
    no_ktp = fields.Char(string="No KTP") 
    npwp = fields.Char(string="NPWP")
    alamat_ktp = fields.Char(string="Alamat KTP")
    alamat_surat = fields.Char(string="Alamat Surat")
    tujuan_transaksi = fields.Char(string="Tujuan Tranksasi")
    bool = fields.Boolean(string="bool")
    """ Buat 4 field per tipe untuk menghindari override field """
    # Attachment Per Type
    customer_attach_ids = fields.One2many('document.customer' ,'document_id',string="Customer Attachment",domain=[('is_customers','=',True)])
    supplier_attach_ids = fields.One2many('document.vendor' ,'document_id',string="Supplier Attachment",domain=[('is_suppliers','=',True)])

    # Proggress Per Type
    customer_progress = fields.Float(string='Progress',compute="_checklist_progress", store=True,
                                      default=0.0)
    supplier_progress = fields.Float(string='Progress',compute="_checklist_progress", store=True,
                                      default=0.0)

    #Document Template Per Type
    customer_template = fields.Many2one('document.template',string="Document Template",compute="_compute_customer_template",inverse=lambda self:True,store=True)
    supplier_template = fields.Many2one('document.template',string="Document Template",compute="_compute_supplier_template",inverse=lambda self:True,store=True)
    appraisal_count=fields.Integer(default=0 , compute="_compute_appraisal_count")
    #contact_type = fields.Many2one('contact.type',string="Contact Type")  #PINDAH KE aos_contact_type BY JU-SAN

    # @api.model
    # def create(self,vals):
    #     if vals.get('vat'):
    #         npwp = self.env['res.partner'].search([('vat','=',vals.get('vat'))])
    #         if npwp:
    #             raise UserError(_('NPWP Pelanggan Tidak Boleh Sama'))
    #     res = super(ResPartner,self).create(vals)
    #     return res

    # def _compute_bool_cust_vendor(self):
    #     for rec in self:
    #         rec.bool = False
    #         if rec._context.get('res_partner_search_mode'):
    #             if rec._context.get('res_partner_search_mode') == 'supplier':
    #                 rec.bool = True


    def _compute_appraisal_count(self) :
        for rec in self :
            res = self.env['vendor.appraisal'].search([('partner_id','=',rec.id)])
            self.appraisal_count = len(res)

   

    def action_view_vendor_appraisal(self):
        action = self.env['ir.actions.act_window']._for_xml_id('aos_vendor_appraisal.action_vendor_appraisal')
        # Get View
        res = self.env['vendor.appraisal'].search([('partner_id','=',self.id)])
        tree, form = self.env.ref('aos_vendor_appraisal.view_vendor_appraisal_tree'), self.env.ref('aos_vendor_appraisal.view_vendor_appraisal_form')
        action['domain'] = f"[('partner_id','=',{self.ids})]"
        if len(res) == 1:
            action['views'] = [(form.id,'form')]
            action['res_id'] = res.id
            action['view_id'] = form.id
        elif len(res) > 1:
            action['view_id'] = tree.id
        else:
            return {'type': 'ir.actions.act_window_close'}
        return action
    
    @api.depends('is_customers')
    def _compute_customer_template(self):
        templates_object = self.env['document.template']
        for line in self:
            #Customer Template
            if line.is_customers:
                templates = templates_object.search([('tenant_type','=','customer')])
                if templates:
                    line.customer_template = templates[0]
                else:
                    line.customer_template = False
            else:
                line.customer_template = False

    @api.depends('is_suppliers')
    def _compute_supplier_template(self):
        templates_object = self.env['document.template']
        for line in self:
            #Supplier Template
            if line.is_suppliers:
                templates = templates_object.search([('tenant_type','=','supplier')])
                if templates:
                    line.supplier_template = templates[0]
                else:
                    line.supplier_template = False
            else:
                line.supplier_template = False




    @api.depends(
    #Partner Field
    'customer_progress',
    'supplier_progress',

    #Attachment Field
    'customer_attach_ids.state',
    'supplier_attach_ids.state',

    )
    def _checklist_progress(self):
        for rec in self:
            #CUSTOMER PROGRESS
            customer_progress = len(rec.customer_attach_ids.filtered(lambda x:x.state == 'done'))
            total_customer = len(rec.customer_attach_ids)
            if customer_progress != 0:
                rec.customer_progress = (customer_progress * 100 ) / total_customer                  
            else:
                rec.customer_progress = 0

            #SUPPLIER PROGRESS
            supplier_progress = len(rec.supplier_attach_ids.filtered(lambda x:x.state == 'done'))
            total_supplier = len(rec.supplier_attach_ids)
            if supplier_progress != 0:
                rec.supplier_progress = (supplier_progress * 100 ) / total_supplier                  
            else:
                rec.supplier_progress = 0


    
    def prepare_document(self,line):
        # set vals name and update field grouping example is_customer set to true
        vals = {
            'name':line.document_type.name,
            'document_id':self._origin.id or self.id,
            'is_required':line.is_required,
        }
        return vals

    @api.onchange('customer_template')
    def onchange_customer_attach_ids(self):
        """
            Unlink first then add new line from template
        """

        attachment_vals = []
        #Attachment Customer
        if self.customer_template:
            for line in self.customer_template.template_ids:
                vals = self.prepare_document(line)
                vals.update({'is_customers':True})
                attachment_vals.append((0,0,vals))
            self.customer_attach_ids = attachment_vals
        
    @api.onchange('supplier_template')
    def onchange_supplier_attach_ids(self):
        """
            Unlink first then add new line from template
        """
        attachment_vals = []
        #Attachment Supplier
        if self.supplier_template:
            for line in self.supplier_template.template_ids:
                vals = self.prepare_document(line)
                vals.update({'is_suppliers':True})
                attachment_vals.append((0,0,vals))
        self.supplier_attach_ids = attachment_vals



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
        if vals.get('state'):
            time = datetime.now()
            under = "Waiting Approval"
            for rec in self :
                body_log = "Contact %s Change State From %s To %s Pada %s" % (rec.name , rec.state , under if vals.get('state') == 'waiting' else vals.get('state') , str(time.strftime("%Y-%m-%d")))
                self.message_post(body = body_log)
        return super(ResPartner , self).write(vals)
        
        
    def validate_document(self):
        customer_attachment = self.customer_attach_ids.filtered(lambda x:x.is_required and not x.file)
        supplier_attachment = self.supplier_attach_ids.filtered(lambda x:x.is_required and not x.file)  

        text = []
        if customer_attachment:
            text.append("Customer Document")
        if supplier_attachment:
            text.append("Supplier Document")

        message_warning = "Some "+(" & ".join(text) if text else "") +" is required to upload file"
        
        if customer_attachment or supplier_attachment:
            raise UserError(message_warning)        

    def draft_wating(self):
        self.validate_document()
        return super(ResPartner, self).draft_wating()
        #write state on contacts_approval_matrix
        # self.write({'state': 'waiting'})
    def waiting_approve(self):
        self.write({'state': 'approve'})
    def reject_contact(self):
        self.write({'state': 'reject'})
    def set_to_draft(self):
        self.write({'state': 'draft'})
        
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    partner_id = fields.Many2one(
    'res.partner', string='Vendor', required=True,
    states=READONLY_STATES, change_default=True,
    tracking=True, domain="['&',('is_suppliers','=',True),('state','=','approve')]",
    help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        required=True, change_default=True, index=True, tracking=1,
        domain="['&',('is_customers','=',True),('state','=','approve')]",)
    
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    
    
    @api.model
    def set_default_domain(self):
        if self._context.get('default_move_type'):
            res = ''
            if self._context.get('default_move_type') == 'in_invoice':
                res = ['&',('is_suppliers','=',True),('state','=','approve')]
            elif self._context.get('default_move_type') == 'out_invoice':
                res = ['&',('is_customers','=',True),('state','=','approve')]
            return res

    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
        states={'draft': [('readonly', False)]},
        check_company=True,
        string='Partner', change_default=True, ondelete='restrict' , domain=set_default_domain)
    is_suppliers = fields.Boolean(related="partner_id.is_suppliers")

# class PropertySale(models.Model):
#     _inherit = 'property.sale'
#
#     partner_id = fields.Many2one(
#         'res.partner', string='Customer',
#         required=True, change_default=True, index=True, tracking=1,
#         domain="['&',('is_customers','=',True),('state','=','approve')]",)
#
# class SubscriptionContract(models.Model):
#     _inherit = 'subscription.contract'
#
#     partner_id = fields.Many2one(
#         'res.partner', string='Customer',
#         required=True, domain="['&',('is_customers','=',True),('state','=','approve')]")
#
# class PropertyUtilites(models.Model):
#     _inherit = 'utilities.meter'
#
#     partner_ids = fields.Many2many('res.partner', 'res_partner_utilities_meter_rel', 'partner_id', 'meter_id', string="Tenant",domain="['&',('is_customers','=',True),('state','=','approve')]")
#
#
# class AccountMove(models.Model):
#     _inherit = 'account.move'
#
#     @api.model
#     def _set_default_bool(self):
#         bool = False
#         if self._context.get('default_move_type') == 'out_invoice':
#                 bool = True
#         return bool
#
#
#     contact_type = fields.Many2one('contact.type',string="Contact Type",readonly=True)
#     no_faktur = fields.Char(string="Nomor Faktur")
#     bool = fields.Boolean(compute="_compute_bool" ,default=_set_default_bool)
#     is_suppliers = fields.Boolean(related="partner_id.is_suppliers")
#
#
#     def _compute_bool(self):
#         self.bool = False
#         if self._context.get('default_move_type'):
#             if self._context.get('default_move_type') == 'out_invoice':
#                 self.bool = True
#         else :
#             self.bool = True
#
#     @api.onchange('partner_id')
#     def onchange_contact_type(self):
#         if self.partner_id.contact_type:
#             self.contact_type = self.partner_id.contact_type
#
#     @api.model
#     def set_default_domain(self):
#         if self._context.get('default_move_type'):
#             res = ''
#             if self._context.get('default_move_type') == 'in_invoice':
#                 res = ['&',('is_suppliers','=',True),('state','=','approve')]
#             elif self._context.get('default_move_type') == 'out_invoice':
#                 res = ['&',('is_customers','=',True),('state','=','approve')]
#             return res
#
#     partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
#         states={'draft': [('readonly', False)]},
#         check_company=True,
#         string='Partner', change_default=True, ondelete='restrict' , domain=set_default_domain)
#
#     @api.model
#     def create(self,vals):
#         if not vals.get('invoice_date') and not vals.get('ref'):
#             if self._context.get('params',{}).get('model') != 'account.move':
#                 return super(AccountMove,self).create(vals)
#             raise UserError(_('Need To Fill Invoice Dates'))
#         return super(AccountMove,self).create(vals)
#
#
#     def deferred_revenues_view(self):
#         self.ensure_one()
#         asset_obj = self.env['account.asset.asset'].search([('invoice_id','=',self.id)])
#         action = {
#             'name': _('Deferred Revenues'),
#             'res_model': 'account.asset.asset',
#             'type': 'ir.actions.act_window',
#             'view_mode': 'form',
#             'view_type':'form',
#             'target':'main',
#         }
#         if len(asset_obj) == 1:
#             action['res_id'] = asset_obj.id
#         elif len(asset_obj) > 1:
#             action['domain'] = [('id','in',asset_obj.ids)]
#         else:
#             return {}
#         return action