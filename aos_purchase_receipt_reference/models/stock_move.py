from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = "stock.move"
    
    partner_ref = fields.Char(string="Vendor Reference", compute="_compute_picking_move_relation", compute_sudo=True)
    picking_batch_id = fields.Many2one('stock.picking.batch', string="Batch No", compute="_compute_picking_move_relation", compute_sudo=True)
    purchase_id = fields.Many2one('purchase.order', string="No PO", compute="_compute_picking_move_relation", compute_sudo=True)
    
    def _prepare_common_svl_vals(self):
        res = super(StockMove,self)._prepare_common_svl_vals()
        if self.picking_id.partner_ref:
            res['description'] = res['description'] + " - " +self.picking_id.partner_ref
        return res
    
    def _compute_picking_move_relation(self):
        for rec in self:
            picking_batch = self.env['stock.picking.batch'].sudo().search([('picking_ids', 'in', rec.picking_id.ids)], limit=1)
            rec.partner_ref = rec.picking_id.partner_ref
            rec.picking_batch_id = picking_batch.id
            rec.purchase_id = rec.purchase_line_id.order_id