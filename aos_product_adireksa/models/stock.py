from odoo import models,api,fields
from datetime import datetime

class StockPickingInherited(models.Model):
    _inherit = 'stock.picking'

    part_number = fields.Char(string="Part Number")
    product_brand = fields.Many2one('product.brand',string="Brand")
    internal_category = fields.Many2one('internal.category',string="Internal Category")
    type_motor = fields.Many2many('type.motor', string="Tipe Motor")
    type_merk = fields.Many2many('type.merk', string="Merk")



# STOCK MOVE LINE
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    part_number = fields.Char(string="Part Number", compute="_compute_part_number", store=True,readonly=True)
    product_brand = fields.Many2one('product.brand',string="Brand", compute="_compute_product_brand",store=True,readonly=True)
    internal_category = fields.Many2one('internal.category',string="Internal Category", compute="_compute_internal_category",store=True,readonly=True)
    type_motor = fields.Many2many('type.motor',string="Tipe Motor", compute="_compute_type_motor",store=True,readonly=True)
    type_merk = fields.Many2many('type.merk', string="Merk", store=True, compute="_compute_type_merk",readonly=True)
   
    # @api.onchange('product_id')
    # def _onchange_product_product(self):
    #     if self.product_id:
    #        self.product_brand = self.product_id.product_brand
    #        self.internal_category = self.product_id.internal_category
    #        self.part_number = self.product_id.part_number
    #        self.type_motor = self.product_id.type_motor
    #        self.type_merk = self.product_id.type_merk


    @api.depends('product_id')
    def _compute_product_brand(self):
        for order in self:
            if not order.product_id:
                order.product_brand = False
                continue
            order = order.with_company(order.company_id)
            order.product_brand = order.product_id.product_brand
    
    @api.depends('product_id')
    def _compute_internal_category(self):
        for order in self:
            if not order.product_id:
                order.internal_category = False
                continue
            order = order.with_company(order.company_id)
            order.internal_category = order.product_id.internal_category
    
    @api.depends('product_id')
    def _compute_part_number(self):
        for order in self:
            if not order.product_id:
                order.part_number = False
                continue
            order = order.with_company(order.company_id)
            order.part_number = order.product_id.part_number
    
    @api.depends('product_id')
    def _compute_type_motor(self):
        for order in self:
            if not order.product_id:
                order.type_motor = False
                continue
            order = order.with_company(order.company_id)
            order.type_motor = order.product_id.type_motor
    
    @api.depends('product_id')
    def _compute_type_merk(self):
        for order in self:
            if not order.product_id:
                order.type_merk = False
                continue
            order = order.with_company(order.company_id)
            order.type_merk = order.product_id.type_merk

# STOCK MOVE
class StockMove(models.Model):
    _inherit = 'stock.move'

    part_number = fields.Char(string="Part Number",compute="_compute_part_number",store=True,readonly=True)
    product_brand = fields.Many2one('product.brand',compute="_compute_product_brand",string="Brand",store=True,readonly=True)
    internal_category = fields.Many2one('internal.category',compute="_compute_internal_category",string="Internal Category",store=True,readonly=True)
    type_motor = fields.Many2many('type.motor',string="Tipe Motor",compute="_compute_type_motor",store=True,readonly=True)
    type_merk = fields.Many2many('type.merk', string="Merk",compute="_compute_type_merk",store=True,readonly=True)

    # @api.onchange('product_id')
    # def _onchange_product_product(self):
    #     if self.product_id:
    #        self.product_brand = self.product_id.product_brand
    #        self.internal_category = self.product_id.internal_category
    #        self.part_number = self.product_id.part_number
    #        self.type_motor = self.product_id.type_motor

    @api.depends('product_id')
    def _compute_product_brand(self):
        for order in self:
            if not order.product_id:
                order.product_brand = False
                continue
            order = order.with_company(order.company_id)
            order.product_brand = order.product_id.product_brand
    
    @api.depends('product_id')
    def _compute_internal_category(self):
        for order in self:
            if not order.product_id:
                order.internal_category = False
                continue
            order = order.with_company(order.company_id)
            order.internal_category = order.product_id.internal_category
    
    @api.depends('product_id')
    def _compute_part_number(self):
        for order in self:
            if not order.product_id:
                order.part_number = False
                continue
            order = order.with_company(order.company_id)
            order.part_number = order.product_id.part_number
    
    @api.depends('product_id')
    def _compute_type_motor(self):
        for order in self:
            if not order.product_id:
                order.type_motor = False
                continue
            order = order.with_company(order.company_id)
            order.type_motor = order.product_id.type_motor
    
    @api.depends('product_id')
    def _compute_type_merk(self):
        for order in self:
            if not order.product_id:
                order.type_merk = False
                continue
            order = order.with_company(order.company_id)
            order.type_merk = order.product_id.type_merk



# STOCK REPORT
class StockQuant(models.Model):
    _inherit = 'stock.quant'
    _order = "create_date DESC"
    
    default_code = fields.Char(string='Internal Reference',compute="_compute_fields",store=True)
    part_number = fields.Char(string='Part Number',compute="_compute_fields",store=True)
    product_brand = fields.Many2one('product.brand',string='Brand',compute="_compute_fields",store=True)
    internal_category = fields.Many2one('internal.category',string="Internal Category",compute="_compute_fields",store=True)
    type_motor = fields.Many2many('type.motor',string="Tipe Motor" ,compute="_compute_type_motor" ,store=True)
    type_merk = fields.Many2many('type.merk', string="Merk" ,compute="_compute_type_merk" ,store=True)
    # create_date = fields.Datetime(string='Created Date',readonly=True) 
    create_uid = fields.Many2one('res.users', 'User', index=True, readonly=True) 
    
    # override fields
    inventory_date = fields.Date( 
        'Created Date', readonly=True,index=True)
    # @api.onchange('product_id')
    # def _onchange_product_product(self):
    #     if self.product_id:
    #        self.product_brand = self.product_id.product_brand
    #        self.internal_category = self.product_id.internal_category
    #        self.part_number = self.product_id.part_number
    #     #    self.type_motor = self.product_id.type_motor
    #     #    self.type_merk = self.product_id.type_merk
    #        self.default_code = self.product_id.default_code 
    @api.model
    def create(self,vals):
        vals.update({'user_id':self.env.user.id})
        return super(StockQuant,self).create(vals) 
 

    def action_set_empty_user(self):
        quants_id = self.env['stock.quant'].search([('user_id','=',False)]) 
        for rec in quants_id:
            rec.user_id = rec.create_uid.id

    @api.depends('product_id')
    def _compute_fields(self):
        for rec in self:
            rec.default_code = rec.product_id.default_code
            rec.part_number = rec.product_id.part_number
            rec.product_brand = rec.product_id.product_brand
            rec.internal_category = rec.product_id.internal_category


    @api.depends('product_id','product_id.internal_category')
    def _compute_internal_category(self):
        for rec in self:
            rec.refresh_boolean = True
            rec.internal_category = rec.product_id.internal_category

    @api.depends('product_id')
    def _compute_type_motor(self):
        for order in self:
            if not order.product_id:
                order.type_motor = False
                continue
            order = order.with_company(order.company_id)
            order.type_motor = order.product_id.type_motor
    
    @api.depends('product_id')
    def _compute_type_merk(self):
        for order in self:
            if not order.product_id:
                order.type_merk = False
                continue
            order = order.with_company(order.company_id)
            order.type_merk = order.product_id.type_merk



    # def _merge_quants(self):
    #       res = super(StockQuant,self)._merge_quants()
    #       res += """,product_brand,
    #       internal_category,
    #       part_number"""
    #       return res
    
    # def _select_additional_fields(self,fields):
    #       res = super(StockQuant,self)._select_additional_fields(fields)
    #       res['product_brand'] = """,product_brand"""   
    #       res['internal_category'] = """,internal_category"""
    #       res['part_number'] = """,part_number"""
    #       return res


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    internal_category = fields.Many2one('internal.category',string="Internal Category",compute="_compute_internal_category",store=True)

    @api.depends('product_id')
    def _compute_internal_category(self):
        for rec in self:
            rec.internal_category = rec.product_id.internal_category





