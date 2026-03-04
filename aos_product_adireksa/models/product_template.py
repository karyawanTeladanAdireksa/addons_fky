from odoo import models,api,fields

class ProductTemplateInherited(models.Model):
    _inherit = 'product.template'

    part_number = fields.Char(string="Part Number")
    product_brand = fields.Many2one('product.brand',string="Brand")
    internal_category = fields.Many2one('internal.category',string="Internal Category")
    type_motor = fields.Many2many('type.motor', string="Tipe Motor")
    type_merk = fields.Many2many('type.merk', string="Merk")
    qty_on_hand_query = fields.Float(
    'Quantity On Hand', compute='_compute_quantities_query', search='_search_qty_available_query',
    compute_sudo=False, digits='Product Unit of Measure',store=True)
    is_discount = fields.Boolean(string="Is Discount")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id, track_visibility='onchange')
    isi_perdus = fields.Float(string="Isi Perdus")
    
    @api.depends(
        'product_variant_ids.qty_available',
    )
    def _compute_quantities_query(self):
        res = self._compute_quantities_dict_query()
        for template in self:
            template.sudo().qty_on_hand_query = res[template.id]['qty_available']

    def _compute_quantities_dict_query(self):
        variants_available = {
            p['id']: p for p in self.product_variant_ids._origin.read(['qty_available'])
        }
        prod_available = {}
        for template in self:
            qty_available = 0
            for p in template.product_variant_ids._origin:
                qty_available += variants_available[p.id]["qty_available"]
            prod_available[template.id] = {
                "qty_available": qty_available,
            }
        return prod_available    
    
class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_discount = fields.Boolean(string="Is Discount",related="product_tmpl_id.is_discount")