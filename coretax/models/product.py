from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    coretax_product_id = fields.Many2one('coretax.product', string="Coretax Product",
                compute='_compute_coretax', inverse='_set_coretax', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.volume')
    def _compute_coretax(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.coretax_product_id = template.product_variant_ids.coretax_product_id
        for template in (self - unique_variants):
            template.coretax_product_id = False

    def _set_coretax(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.coretax_product_id = template.coretax_product_id
    
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    coretax_product_id = fields.Many2one('coretax.product', string="Coretax Product")
    # coretax_uom_id = fields.Many2one('coretax.uom', string="Coretax UoM")


class UoM(models.Model):
    _inherit = 'uom.uom'

    coretax_uom_id = fields.Many2one('coretax.uom', string="Coretax UoM")