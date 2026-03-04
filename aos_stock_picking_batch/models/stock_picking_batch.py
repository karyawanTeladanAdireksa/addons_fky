# -*- coding: utf-8 -*-

from odoo import api, models,fields
from odoo.osv.expression import AND

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    partner_id = fields.Many2one('res.partner',string="Customers")
    customer_group_id = fields.Many2one('adireksa.customer.target',string="Customer Group")
    keterangan = fields.Text(string="Reference")

    #OVERRIDE
    @api.depends('company_id', 'picking_type_id', 'state','customer_group_id','partner_id')
    def _compute_allowed_picking_ids(self):
        allowed_picking_states = ['waiting', 'confirmed', 'assigned']
        for batch in self:
            domain_states = list(allowed_picking_states)
            # Allows to add draft pickings only if batch is in draft as well.
            if batch.state == 'draft':
                domain_states.append('draft')
            domain = [
                ('company_id', '=', batch.company_id.id),
                ('state', 'in', domain_states),
            ]
            if not batch.is_wave:
                domain = AND([domain, [('immediate_transfer', '=', False)]])
            if batch.picking_type_id:
                domain += [('picking_type_id', '=', batch.picking_type_id.id)]
            if batch.partner_id :
                domain += [('partner_id', '=', batch.partner_id.id)]
            elif batch.customer_group_id :
                domain += [('partner_id', 'in', batch.customer_group_id.partner_ids.ids)]
            batch.allowed_picking_ids = self.env['stock.picking'].search(domain)