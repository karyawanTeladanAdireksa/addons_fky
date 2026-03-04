from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class BackorderWizard(models.TransientModel):
    _name = 'backorder.wizard'
    _description = 'Backorder Wizard'

    @api.model
    def default_get(self,fields):
        res = super(BackorderWizard,self).default_get(fields)
        po_obj = self.env['purchase.order'].browse(self._context.get('active_id'))
        line_id = []
        for rec in po_obj.order_line:
            if rec.product_qty != rec.qty_received:
                line_id.append((0,0,
                    {'product_id':rec.product_id.id,
                     'qty':rec.product_qty - rec.qty_received,
                     'price':rec.price_unit,
                     'name':rec.name,
                     }))
        res['backorder_line_ids'] = line_id
        res['po_id'] = po_obj
        return res

    name = fields.Char(string="name",default="Purchase BackOrder")
    backorder_line_ids = fields.One2many('backorder.line.wizard','backorder_id')
    po_id = fields.Many2one('purchase.order')


    def btn_confirm(self):
        order_line = []
        for rec in self.backorder_line_ids:
            order_line.append((0,0,{
                'product_id':rec.product_id.id,
                'product_qty':rec.qty,
                'price_unit':rec.price_after if rec.price_after else rec.price,
                'name':rec.name,
                }))
        po_obj = self.env['purchase.order'].create({'parent_id':self.po_id.id,'currency_id':self.po_id.currency_id.id,'partner_id':self.po_id.partner_id.id,'order_line':order_line})
        picking = self.po_id.picking_ids.filtered(lambda x:x.state != 'done')
        picking.write({'state':'cancel'})
        picking.move_lines.write({'state':'cancel'})
        for move in picking.move_ids_without_package:
            move.write({'state':'cancel'})
        self.po_id.write({'back_bool':True})
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "views": [[False, "form"]],
            "res_id": po_obj.id,
        }

    
class BackorderLineWizard(models.TransientModel):
    _name = 'backorder.line.wizard'
    _description = 'Backorder Line Wizard'

    name=fields.Char()
    backorder_id = fields.Many2one('backorder.wizard')
    product_id = fields.Many2one('product.product',string="Product Id")
    qty = fields.Integer(string="Qty")
    price = fields.Monetary(string="Unit Price",currency_field='currency_id')
    disc = fields.Float(string="Discount")
    price_after = fields.Monetary(string="Price After Discount",readonly=True,currency_field='currency_id')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(related="backorder_id.po_id.currency_id", string='Currency', readonly=False)

    @api.onchange('price','disc')
    def onchange_price_after(self):
        self.price_after = self.price - ((self.price / 100) * self.disc ) 