from odoo import models, fields,api


class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    kode_barang  = fields.Char(string="kode_barang", related='product_id.default_code')
    #sparepart  = fields.Char(string="Sparepart", related='product_id.default_code')
    sparepart  = fields.Char(string="Sparepart", related='product_id.hs_code')
    #kode_barang  = fields.Char(string="Kode Barang", related='product_id.hs_code')
    # jenis_motor = fields.Char(string="Jenis Motor", related='product_id.product_brand_id.name')
    jenis_motor = fields.Many2many('product.template.attribute.line',compute="_compute_product_attribute", string='Jenis Motor')

    @api.depends('product_id')
    def _compute_product_attribute(self):
        for rec in self:
            rec.jenis_motor = rec.product_id.attribute_line_ids.ids

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    kode_barang  = fields.Char(string="Kode Barang", related='product_id.default_code')
    #sparepart  = fields.Char(string="Sparepart", related='product_id.default_code')
    sparepart  = fields.Char(string="Part Number", related='product_id.hs_code')
    kode_barang  = fields.Char(string="Kode Barang", related='product_id.hs_code')
    # jenis_motor = fields.Char(string="Jenis Motor", related='product_id.product_brand_id.name')
    jenis_motor = fields.Many2many('product.template.attribute.line',compute="_compute_product_attribute", string='Jenis Motor')

    @api.depends('product_id')
    def _compute_product_attribute(self):
        for rec in self:
            rec.jenis_motor = rec.product_id.attribute_line_ids.ids

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    kode_barang  = fields.Char(string="Kode Barang", related='product_id.default_code')
    sparepart  = fields.Char(string="Part Number", related='product_id.hs_code')
    # jenis_motor = fields.Char(string="Jenis Motor", related='product_id.product_brand_id.name')
    jenis_motor = fields.Many2many('product.template.attribute.line',compute="_compute_product_attribute", string='Jenis Motor')

    @api.depends('product_id')
    def _compute_product_attribute(self):
        for rec in self:
            rec.jenis_motor = rec.product_id.attribute_line_ids.ids
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    kode_barang  = fields.Char(string="Kode Barang", related='product_id.default_code')
    sparepart  = fields.Char(string="Sparepart", related='product_id.hs_code')
    # jenis_motor = fields.Char(string="Jenis Motor", related='product_id.product_brand_id.name')
    jenis_motor = fields.Many2many('product.template.attribute.line',compute="_compute_product_attribute", string='Jenis Motor')

    @api.depends('product_id')
    def _compute_product_attribute(self):
        for rec in self:
            rec.jenis_motor = rec.product_id.attribute_line_ids.ids
class StockMove(models.Model):
    _inherit = 'stock.move'

    kode_barang  = fields.Char(string="Kode Barang", related='product_id.default_code')
    sparepart  = fields.Char(string="Sparepart", related='product_id.hs_code')
    # jenis_motor = fields.Char(string="Jenis Motor", related='product_id.product_brand_id.name')
    jenis_motor = fields.Many2many('product.template.attribute.line',compute="_compute_product_attribute", string='Jenis Motor')

    @api.depends('product_id')
    def _compute_product_attribute(self):
        for rec in self:
            rec.jenis_motor = rec.product_id.attribute_line_ids.ids
# class StdItemMR(models.Model):
#     _inherit = 'std.item.mr'

#     kode_barang  = fields.Char(string="Kode Barang", related='product.default_code')
#     sparepart  = fields.Char(string="Sparepart", related='product.hs_code')
#     # jenis_motor = fields.Char(string="Jenis Motor", related='product.product_brand_id.name')
#     jenis_motor = fields.Many2many(related='product.attribute_line_ids', string='Jenis Motor')



class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = 'product.template'

    hs_code = fields.Char(string="Part Number", help="Standardized code for international shipping and goods declaration",)

    #set all product variant
    @api.onchange('hs_code')
    def onchange_hs_code_variant(self):
        product = self.env['product.product'].search([('product_tmpl_id','=',self.id),('hs_code','=',False)])
        product.sudo().update({'hs_code':self.hs_code})

class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = "product.product"

    hs_code = fields.Char(string="Part Number",help="Standardized code for international shipping and goods declaration",)