# from random import randint
from odoo import models,api,fields

class ProductBrand(models.Model):
    _name ="product.brand"
    _description = "Product Brand"

    name = fields.Char("Name", required=True, size=100)
    product_brand = fields.Many2one('product.brand',string="Brand")
    part_number = fields.Char(string="Part Number")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')

    
class InternalCategory(models.Model):
    _name ="internal.category" 
    _description = "Internal Category"

    name = fields.Char("Name", required=True, size=100)
    internal_category = fields.Many2one('internal.category',string="Internal Category")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')

# FIELDS TIPE MOTOR
class TypeMotor(models.Model):
    _name ="type.motor"
    _description = "Type Motor"
    
    name = fields.Char("Name", required=True, size=100)
    type_motor = fields.Many2many('type.motor.line',string="Tipe Motor")
    color = fields.Integer('Color')
    active = fields.Boolean(string="Active",default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')

# FIELDS MERK
class TypeMerk(models.Model):
    _name ="type.merk"
    _description = "Merk"
    
    name = fields.Char("Name", required=True, size=100)
    type_merk = fields.Many2many('type.merk.line',string="Merk")
    color = fields.Integer('Color')
    active = fields.Boolean(string="Active",default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')


class ResPartner(models.Model):
    _inherit = "res.partner"

    internal_category = fields.Many2one('internal.category',string="Internal Category",store=True)
