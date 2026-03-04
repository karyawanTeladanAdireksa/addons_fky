# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class AccountTax(models.Model):
    _inherit = 'account.tax'
     
    is_withholding = fields.Boolean(help='Set this field to true if this tax is for tax witholding')

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale'),('is_withholding','=',False)], default=lambda self: self.env.user.company_id.account_sale_tax_id)
    supplier_taxes_id = fields.Many2many('account.tax', 'product_supplier_taxes_rel', 'prod_id', 'tax_id', string='Vendor Taxes', help='Default taxes used when buying the product.',
        domain=[('type_tax_use', '=', 'purchase'),('is_withholding','=',False)], default=lambda self: self.env.user.company_id.account_purchase_tax_id)
    taxes_wth_id = fields.Many2many('account.tax', 'product_taxes_wth_rel', 'prod_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes Wth',
        domain=[('type_tax_use', '=', 'sale'),('is_withholding','=',True)])
    supplier_taxes_wth_id = fields.Many2many('account.tax', 'product_supplier_taxes_wth_rel', 'prod_id', 'tax_id', string='Vendor Taxes Wth', help='Default taxes used when buying the product.',
        domain=[('type_tax_use', '=', 'purchase'),('is_withholding','=',True)])
    
class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'
    
    tax_id = fields.Many2many('account.tax', 'partner_category_taxes_rel', 'category_id', 'tax_id', string='Customer Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    tax_wth_id = fields.Many2many('account.tax', 'partner_category_taxes_wth_rel', 'category_id', 'tax_id', string='Customer Withholding Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

class ResPartner(models.Model):    
    _inherit = "res.partner"
    
    day_tt = fields.Char('Day Transfer')
    day_invoice = fields.Char('Day Invoice')
    vendor_tax = fields.Char('Vendor Tax No.')
    pkp_no = fields.Char('PKP No.')
    admin_tax_name = fields.Char('Admin Tax Name')
    admin_tax_email = fields.Char('Admin Tax Email')
    admin_tax_wp = fields.Char('WP')
    
    supplier_is_taxable = fields.Boolean(string='Vendor Is Taxable')
    customer_is_taxable = fields.Boolean(string='Customer Is Taxable')

    taxes_id = fields.Many2many('account.tax', 'partner_taxes_rel', 'part_id', 'tax_id', string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale'),('is_withholding','=',False)])
    taxes_wth_id = fields.Many2many('account.tax', 'partner_taxes_wth_rel', 'part_id', 'tax_id', string='Customer Taxes Wth',
        domain=[('type_tax_use', '=', 'sale'),('is_withholding','=',True)])
    supplier_taxes_id = fields.Many2many('account.tax', 'partner_supplier_taxes_rel', 'part_id', 'tax_id', string='Vendor Taxes',
        domain=[('type_tax_use', '=', 'purchase'),('is_withholding','=',False)])
    supplier_taxes_wth_id = fields.Many2many('account.tax', 'partner_supplier_wth_taxes_rel', 'part_id', 'tax_id', string='Vendor Taxes Wth',
        domain=[('type_tax_use', '=', 'purchase'),('is_withholding','=',True)])
    
    @api.onchange('category_id')
    def _onchange_tags(self):
        self.ensure_one()
        if not self.category_id:
            return
        self.taxes_wth_id = self.taxes_id = []
        self.taxes_wth_id = [(6, 0, self.category_id.tax_wth_id.ids)]
        self.taxes_id = [(6, 0, self.category_id.tax_id.ids)]
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
