from odoo import models,api,fields

# SALE ORDER LINE
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    part_number = fields.Char(string="Part Number",compute="_compute_part_number",store=True,readonly=True)
    product_brand = fields.Many2one('product.brand',string="Brand",compute="_compute_product_brand",store=True,readonly=True)
    internal_category = fields.Many2one('internal.category',string="Internal Category",compute="_compute_internal_category",store=True,readonly=True)
    type_motor = fields.Many2many('type.motor',string="Tipe Motor",compute="_compute_type_motor",store=True,readonly=True)
    type_merk = fields.Many2many('type.merk', string="Merk",compute="_compute_type_merk",store=True,readonly=True)

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




# REPORT SALE
class SaleReport(models.Model):
    _inherit = 'sale.report'
    
    part_number = fields.Char(string="Part Number")
    product_brand = fields.Many2one('product.brand',string="Brand")
    internal_category = fields.Many2one('internal.category',string="Internal Category")
    type_motor = fields.Many2many('type.motor',relation='sale_order_line_type_motor_rel',column1='sale_order_line_id', column2='type_motor_id',string="Tipe Motor")
    type_merk = fields.Many2many('type.merk',relation='sale_order_line_type_merk_rel',column1='sale_order_line_id', column2='type_merk_id',string="Merk")

    # def _from_sale(self, from_clause=''):
    #     res = super(SaleReport,self)._from_sale(from_clause)
    #     res +="""inner join sale_order_line_type_merk_rel sol_merk on (sol_merk.sale_order_line_id = l.id)"""
    #     return res

    # def group by sale
    def _group_by_sale(self,groupby=''):
          res = super(SaleReport,self)._group_by_sale(groupby)
          res +=""",l.product_brand,
          l.id,
          l.internal_category,
          l.part_number"""
          
          return res
    
    def _select_sale(self, fields=None):
        res = super(SaleReport, self)._select_sale(fields) + ", l.internal_category as internal_category,l.product_brand as product_brand,l.part_number as part_number"
        res += """,(SELECT ARRAY_AGG(sale_order_line_type_motor_rel.type_motor_id) FROM sale_order_line_type_motor_rel where sale_order_line_id = l.id) as type_motor """
        res += """,(SELECT ARRAY_AGG(sale_order_line_type_merk_rel.type_merk_id) FROM sale_order_line_type_merk_rel where sale_order_line_id = l.id) as type_merk """
        return res
    
    # def _select_additional_fields(self,fields):
    #       res = super(SaleReport,self)._select_additional_fields(fields)
    #       res['product_brand'] = """,l.product_brand"""   
    #       res['internal_category'] = """,l.internal_category"""
    #       res['part_number'] = """,l.part_number"""
    #       return res
    