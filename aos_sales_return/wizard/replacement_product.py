from odoo import models,fields,api,Command,_
from odoo.tools import float_compare
from odoo.exceptions import UserError
from collections import defaultdict
class ReplacementProduct(models.TransientModel):
    _name = "replacement.product.wizard"

    replacement_ids = fields.One2many('replacement.product.line.wizard','wiz_id',string="Replacement")
    return_line_id = fields.Many2one('sales.return.line')
    
    @api.model
    def default_get(self,fields_list=None):
        res = super(ReplacementProduct,self).default_get(fields_list)
        return_line_id = self.env['sales.return.line'].browse(self.env.context.get('return_line_id'))
        res['return_line_id'] = return_line_id.id
        if not return_line_id.replacement_product_ids:
            return res
        res['replacement_ids'] = []
        if return_line_id.replacement_product_ids:
            for line in return_line_id.replacement_product_ids:
                res['replacement_ids']  += [(0,0,{'product_id':line.product_id.id,'brand':line.brand_id.id,'qty':line.qty,'price_unit':line.price_unit or line.product_id.standard_price})]
        return res



    @api.model
    def create(self,vals):
        precision = self.env['decimal.precision'].precision_get('Product Price')
        return_line_id = self.env['sales.return.line'].browse(self.env.context.get('return_line_id')) 
        selisih_harga = return_line_id.price_subtotal * (5 / 100)
        if 'replacement_ids' in vals:
            replacement_amount = sum(list(map(lambda item: item[-1]['price_unit'] * item[-1]['qty'] ,vals['replacement_ids'])))
            if float_compare(replacement_amount,return_line_id.price_subtotal + selisih_harga,precision_digits= precision) > 0 :
                raise UserError(f"Total harga pergantian barang lebih besar 5% dari harga total")
            
            elif float_compare(replacement_amount,return_line_id.price_subtotal - selisih_harga,precision_digits= precision) < 0 :
                raise UserError(f"Total harga pergantian barang lebih kecil 5% dari harga total") 
            
            # if float_compare(replacement_amount, return_line_id.price_subtotal,precision_digits= precision) > 0:
            #     raise UserError(f"Price Subtotal More Than {return_line_id.price_subtotal:,.2f}")

        result = super(ReplacementProduct,self).create(vals)
        replacement_obj = document_to_unlink = self.env['replacement.product']
        brand_obj = document_to_unlink = self.env['replacement.brand']
        qty_obj = document_to_unlink = self.env['replacement.qty']
        replacement_obj = []
        brand_obj = []
        qty_obj = []

        for line in result.replacement_ids:           
            replacement_obj.append(Command.create({'product_id':line.product_id.id,'brand_id':line.brand.id,'name':line.product_id.name,'qty':line.qty,'price_unit':line.price_unit,'return_line_id':result.return_line_id.id}))           
            brand_obj.append(Command.create({'brand_id':line.brand.id,'name':line.brand.name,'return_line_id':result.return_line_id.id})) 
            qty_obj.append(Command.create({'qty':line.qty,'name':line.qty,'return_line_id':result.return_line_id.id}))  
        if result.return_line_id.replacement_product_ids:
            document_to_unlink = result.return_line_id.replacement_product_ids
            document_to_unlink.unlink()
        if result.return_line_id.brand_replacement_ids:
            document_to_unlink = result.return_line_id.brand_replacement_ids
            document_to_unlink.unlink()
        if result.return_line_id.replacement_qty_ids:
            document_to_unlink = result.return_line_id.replacement_qty_ids 
            document_to_unlink.unlink() 
        #Recreate
        result.return_line_id.replacement_product_ids = replacement_obj 
        result.return_line_id.brand_replacement_ids = brand_obj 
        result.return_line_id.replacement_qty_ids = qty_obj
        return result

    def button_confirm(self):
        return {'type':'ir.actions.client','tag':'reload'}
    
    def button_discard(self):
        return self.env.cr.rollback()
    

class ReplamentProductLine(models.TransientModel):
    _name = "replacement.product.line.wizard"


    wiz_id = fields.Many2one('replacement.product.wizard',"wiz")
    quantity_on_hand = fields.Float(string="Quantity On Hand" ,compute="_compute_quantity_on_hand" ,track_visibility='onchange')
    product_id = fields.Many2one('product.product',string="Product") 
    brand = fields.Many2one('product.brand',string="Brand", required=True) 
    qty = fields.Float(string="Qty",required=True,default=1)  
    # qty_available = fields.Float(
    #     'Quantity On Hand', compute='_compute_quantities_available', compute_sudo=False, digits='Product Unit of Measure')
    price_unit = fields.Float(string="Price Unit",required=True)
    price_subtotal = fields.Float(string="Price Subtotal",compute="_compute_price_subtotal")
 
    @api.depends('price_unit','qty') 
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.qty

    @api.onchange('product_id')
    def _onchange_price_unit(self):
        self.brand = self.product_id.product_brand
        self.price_unit = self.product_id.list_price
    

    @api.depends('product_id')
    def _compute_quantity_on_hand(self):
        for line in self:
            line.quantity_on_hand = line.product_id.with_context(warehouse=line.wiz_id.return_line_id.return_id.warehouse_id.id).qty_available 