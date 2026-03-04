from odoo import models,fields,api


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"


    is_return_in = fields.Boolean(string="Return Masuk")
    is_return_out = fields.Boolean(string="Return Keluar")
    
    
    @api.onchange('is_return_in')
    def onchange_picking_type_return_in(self):
        if self.is_return_in:
            self.is_return_out = False
            
    @api.onchange('is_return_out')
    def onchange_picking_type_return_out(self):
        if self.is_return_out:
            self.is_return_in = False
        
class StockPicking(models.Model):
    _inherit = "stock.picking"

    sales_return_id = fields.Many2one('sales.return',string="Sales Return")

class StockMove(models.Model):
    _inherit = "stock.move"

    incoming_sales_return_line_id = fields.Many2one('sales.return.line','Sales Return Line Receipt')
    outgoing_sales_return_line_id = fields.Many2one('sales.return.line','Sales Return Line Delivery')
    sales_return_id = fields.Many2one('sales.return','Sales Return',compute="_compute_sales_return",store=True)

    @api.depends('outgoing_sales_return_line_id','incoming_sales_return_line_id')
    def _compute_sales_return(self):
        for move in self:
            move.sales_return_id = move.outgoing_sales_return_line_id.return_id or move.incoming_sales_return_line_id.return_id

    def _prepare_merge_moves_distinct_fields(self):
        res = super(StockMove,self)._prepare_merge_moves_distinct_fields()
        res.append('incoming_sales_return_line_id')
        res.append('outgoing_sales_return_line_id')
        res.append('sales_return_id')
        return res