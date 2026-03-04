from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    outstanding_qty = fields.Integer(string="Qty Outstanding", compute="_compute_outstanding_moves_qty")
    
    @api.model
    def _get_domain_outstanding_moves(self, product_tmpl, companies):
        vendorLocation = self.env.ref('stock.stock_location_suppliers', raise_if_not_found=False)
        domain = [
            ('product_id.product_tmpl_id', '=', product_tmpl.id),
            ('location_id', '=', vendorLocation.id),
            ('state','=','assigned'),
            ('location_id.usage', 'not in', ('internal', 'transit')), ('location_dest_id.usage', 'in', ('internal', 'transit')),
            ('company_id', 'in', companies.ids),
            ('picking_id.state', '!=', 'cancel'),
        ]
        return domain
    
    def _compute_outstanding_moves_qty(self):
        for rec in self:
            Moves = self.env['stock.move'].sudo()
            companies = rec.company_id if rec.company_id else self.env.companies
            outstanding_qty = Moves.read_group(self._get_domain_outstanding_moves(rec, companies), ['product_uom_qty'], ['location_id'])
            if outstanding_qty:
                rec.outstanding_qty = outstanding_qty[0]['product_uom_qty']
            else:
                rec.outstanding_qty = 0.0
            
    def action_view_moves(self):
        ctx = dict(self._context)
        companies = self.company_id if self.company_id else self.env.companies
        tree_view = self.env.ref('stock.view_move_tree')
        return {
            'name': (_("Incoming Qty Moves")),
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'domain': self._get_domain_outstanding_moves(self, companies),
            'views': [(tree_view.id, 'tree'), (False, 'form')],
            'context': ctx,
            'type': 'ir.actions.act_window',
        }