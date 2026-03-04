# -*- coding: utf-8 -*-

from odoo import api, models,fields,_
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse")
    is_pack =fields.Boolean(related="warehouse_id.is_pack")

    def check_desimal(self,vals):
        if vals.get('order_line'):
            pack = self.is_pack or self._context.get('is_pack')
            for rec in vals.get('order_line'):
                if rec[2] != False and pack == True and rec[2].get('product_packaging_qty'):
                    list_val = list(str(rec[2].get('product_packaging_qty')))
                    try:
                        dot_index_1 =  list_val.index('.') + 1
                    except ValueError:
                        list_val.append(0)
                        dot_index_1 = -1
                    if int(list_val[dot_index_1]) != 0 or list_val[-1] != 0:
                        raise UserError(_('Packaging Dus Tidak Boleh Decimal'))

    def write(self,vals):
        # self.check_desimal(vals)
        res = super(SaleOrder,self).write(vals)
        if self.is_pack == True or self.warehouse_id.is_pack == True:
            for rec in self.order_line:
                if not rec.product_packaging_id and rec.detailed_type != 'service':
                    raise UserError(_('Packaging Dus Tidak Boleh Kosong'))
                list_val = list(str(rec.product_packaging_qty))
                try:
                    dot_index_1 =  list_val.index('.') + 1
                except ValueError:
                    list_val.append(0)
                    dot_index_1 = -1
                if int(list_val[dot_index_1]) != 0 or int(list_val[-1]) != 0:
                    raise UserError(_('Packaging Dus Tidak Boleh Decimal'))
        return res 
    
    @api.model
    def create(self,vals):
        res = super(SaleOrder,self).create(vals)
        self.with_context(is_pack = res.is_pack).check_desimal(vals)
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    detailed_type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),('product', 'Storable Product')],related="product_id.detailed_type")
