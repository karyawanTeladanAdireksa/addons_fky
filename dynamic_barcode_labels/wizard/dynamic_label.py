# -*- encoding: utf-8 -*-

from odoo import fields, api, models, _


class DynamicLabelWizard(models.TransientModel):
    _name = 'dynamic.label.wizard'
    _description = 'Dynamic Label Wizard'

    type = fields.Selection([
        ('price_tag', 'Price Tag')
    ], string="Type", default='price_tag')
    total_barcode = fields.Integer(string='Total No.of Barcode', default=65) 
    barcode_packaging_id = fields.Many2one(comodel_name="product.packaging",string="Packaging Barcode") 
    product_packaging_ids = fields.Many2many(comodel_name="product.product")

    # FUNGSI PEMISAH NAMA PRODUK
    @api.model
    def default_get(self, fields):
        res = super(DynamicLabelWizard, self).default_get(fields)
        if not res.get('product_packaging_ids'):
            template_product = self.env['product.template'].browse(self.env.context.get('active_ids'))
            res.update({'product_packaging_ids':[(6,0,template_product.product_variant_ids.ids)]}) 
        return res


    # @api.multi
    def print_report(self):
        data = {}
        data_list = []
        data['ids'] = self.env.context.get('active_ids', [])
        barcode_packaging = self.barcode_packaging_id.barcode
        
        data['model'] = self.env.context.get('active_model', 'product.template')
        data['form'] = self.read(['type', 'total_barcode','barcode_packaging_id'])[0] 
        product_recs = self.env[data['model']].browse(data['ids']) 
        return_value = False
        if not barcode_packaging:
            barcode_packaging = product_recs.barcode
        data_dict = {'code': product_recs.name, 'barcode_packaging': barcode_packaging,
                        'total_barcode': self.total_barcode,
                        'tipe_motor': ', '.join(product_recs.type_motor.mapped('name'))}
        data_list.append(data_dict)
        data['form'].update({'data_values': data_list})
                
            

        if self.type == 'price_tag':
            if self.env.context.get('is_mini'):
                return_value = self.env.ref('dynamic_barcode_labels.action_report_dynamic_label_mini').report_action(self.ids, data=data)
            else:
                return_value = self.env.ref('dynamic_barcode_labels.action_report_dynamic_label').report_action(self.ids, data=data)
        return return_value
    

class ProductPackaging(models.Model):  
    _inherit = 'product.packaging'
    _description = 'Product Packaging'

    barcode_packaging_id = fields.Many2one(comodel_name="product.packaging",string="Barcode") 
   
