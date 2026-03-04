from odoo import models,api,fields


# PURCHASE ORDER LINE
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    part_number = fields.Char(string="Part Number",compute="_compute_part_number",store=True,readonly=True)
    product_brand = fields.Many2one('product.brand',compute="_compute_product_brand",string="Brand",store=True,readonly=True)
    internal_category = fields.Many2one('internal.category',string="Internal Category",compute="_compute_internal_category",store=True,readonly=True)
    type_motor = fields.Many2many('type.motor',string="Tipe Motor",compute="_compute_type_motor",store=True,readonly=True)
    type_merk = fields.Many2many('type.merk', string="Merk",compute="_compute_type_merk",store=True,readonly=True)
    internal_notes = fields.Char(string="Internal Notes")
    
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
    
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.description_purchase
        if product_lang.display_name: 
            name

        return name
# PURCHASE REPORT
class PurchaseReport(models.Model):
    _inherit = 'purchase.report'
    
    part_number = fields.Char(string="Part Number")
    product_brand = fields.Many2one('product.brand',string="Brand")
    internal_category = fields.Many2one('internal.category',string="Internal Category")
    type_motor = fields.Many2many('type.motor',relation='purchase_order_line_type_motor_rel',column1='purchase_order_line_id', column2='type_motor_id',string="Tipe Motor")
    type_merk = fields.Many2many('type.merk',relation='purchase_order_line_type_merk_rel',column1='purchase_order_line_id', column2='type_merk_id', string="Merk")

    # def _from(self):
    #     res = super(PurchaseReport,self)._from()
    #     res +="""left join purchase_order_line_type_motor_rel pol on (pol.purchase_order_line_id = l.id)
    #             left join type_motor motor on (motor.id = pol.purchase_order_line_id)
    #             left join purchase_order_line_type_merk_rel pol_merk on (pol_merk.purchase_order_line_id = l.id)
    #             left join type_merk merk on (merk.id = pol_merk.purchase_order_line_id)"""
        
    
    def _select(self):
          res = super(PurchaseReport,self)._select()
          res += """,l.product_brand,
          l.internal_category,
          l.part_number""" 
          return res 
    
    def _group_by(self):
        res = super(PurchaseReport,self)._group_by()
        res += """,l.product_brand,
        l.internal_category,
        l.part_number"""
        return res

     
    def _select_additional_fields(self,fields):
          res = super(PurchaseReport,self)._select_additional_fields(fields)
          res['product_brand'] = """,l.product_brand"""   
          res['internal_category'] = """,l.internal_category"""
          res['part_number'] = """,l.part_number"""
        #   res['id'] = """,motor.id"""
        #   res['id'] = """,merk.id"""
          return res
    