from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError
import ast
from datetime import datetime, timedelta, date

class StockPicking(models.Model):
    _inherit = "stock.picking"

    expiry_date = fields.Date(string="Expiry Date",readonly=False)

    @api.model
    def create(self,vals):
        res = super(StockPicking,self).create(vals)
        if res.picking_type_name:
            if res.picking_type_name == 'Delivery Orders':
                res.write({'expiry_date':res.create_date.date() + timedelta(days=res.partner_id.expiry_count)})
        return res
        


    def _set_cancel_expiry_backorder(self):
        self = self.env['stock.picking'].search([
            ('backorder_id','!=',False),
            ('picking_type_id.code','=','outgoing'),
            ('partner_id.expiry_bool','=',True),
            ('state','!=','done' or 'cancel'),
            ('expiry_date','=',fields.date.today())
            ])
        for rec in self :
                rec.write({'state':'cancel'})
