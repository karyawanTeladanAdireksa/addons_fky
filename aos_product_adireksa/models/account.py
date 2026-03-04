from odoo import models,api,fields



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    part_number = fields.Char(string="Part Number",compute="_compute_part_number",store=True,readonly=True)
    product_brand = fields.Many2one('product.brand',string="Brand",compute="_compute_product_brand",store=True,readonly=True)
    internal_category = fields.Many2one('internal.category',string="Internal Category",compute="_compute_internal_category",store=True,readonly=True)
    type_motor = fields.Many2many('type.motor',string="Tipe Motor",compute="_compute_type_motor",store=True,readonly=True)
    type_merk = fields.Many2many('type.merk', string="Merk",compute="_compute_type_merk",store=True,readonly=True)
    city = fields.Char(string="City", compute="_compute_fields", store=True) 
    state_id = fields.Many2one('res.country.state', string="State", compute="_compute_fields",store=True)



    # @api.onchange('product_id')
    # def _onchange_product_product(self):
    #     if self.product_id:
    #        self.product_brand = self.product_id.product_brand
    #        self.internal_category = self.product_id.internal_category
    #        self.part_number = self.product_id.part_number
    #        self.type_motor = self.product_id.type_motor
    #        self.type_merk = self.product_id.type_merk

    @api.depends('move_id')
    def _compute_fields(self):
        for account in self:
            if account.move_id:
                account.city = account.move_id.partner_id.city
                account.state_id = account.move_id.partner_id.state_id.id


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
    


# INVOICE REPORT
class InvoiceReport(models.Model):
    _inherit = 'account.invoice.report'
    
    part_number = fields.Char(string="Part Number")
    product_brand = fields.Many2one('product.brand',string="Brand")
    internal_category = fields.Many2one('internal.category',string="Internal Category")
    type_motor = fields.Many2many('type.motor',relation='account_move_line_type_motor_rel',column1='account_move_line_id', column2='type_motor_id',string="Tipe Motor")
    type_merk = fields.Many2many('type.merk',relation='account_move_line_type_merk_rel',column1='account_move_line_id', column2='type_merk_id', string="Merk")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string="State")

    def _select(self):
          res = super(InvoiceReport,self)._select() 
          res += """,line.product_brand,
          line.internal_category,
          line.part_number,
          line.city,
          line.state_id"""
          return res

     
    def _select_additional_fields(self,fields):
          res = super(InvoiceReport,self)._select_additional_fields(fields)
          res['product_brand'] = """,line.product_brand"""   
          res['internal_category'] = """,line.internal_category"""
          res['part_number'] = """,line.part_number"""
          res['city'] = """,line.city"""
          res['state_id'] = """,line.state_id"""
          return res
    
