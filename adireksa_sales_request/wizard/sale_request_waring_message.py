from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class SRMessage(models.TransientModel):
    _name = "sr.message"

    message = fields.Char(String='Message')

    def action_yes(self):
        sale_request = self.env['sale.request'].browse(self._context.get('active_id'))
        vals = {}
        for record in sale_request:
            vals['partner_id'] = record.partner_id.id
            vals['sale_request_id'] = record.id
            vals['warehouse_id'] = record.warehouse_id.id
            vals['date_order'] = record.date_order
            vals['payment_term_id'] = record.payment_term_id.id
            line_data = []
            check_all_partial_count = 0
            for line in record.request_line:
                if not line.sale_qty:
                    qty_available = line.product_id.with_context({'warehouse': sale_request.warehouse_id.id}).qty_available
                    final_qty = qty_available
                    if line.product_uom_qty < qty_available:
                        final_qty = line.product_uom_qty
                        check_all_partial_count += 1
                    line_vals = {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom_qty': final_qty,
                        'price_unit': line.price_unit,
                        'tax_id': [(6,0,line.tax_id.ids)]
                    }
                    line.write({'sale_qty': final_qty})
                    line_data.append((0, 0, line_vals))
                else:
                    quotation_ids = self.env['sale.order'].search([('sale_request_id', '=', sale_request.id)])
                    lines_ids = quotation_ids.mapped('order_line').filtered(lambda a: a.product_id == line.product_id)
                    product_uom_qty = sum(lines_ids.mapped('product_uom_qty'))
                    qty_available = line.product_id.with_context({'warehouse': sale_request.warehouse_id.id}).qty_available
                    remaining_qty = qty_available - product_uom_qty
                    check_all_partial_count = 1
                    if line.product_uom_qty != line.sale_qty and remaining_qty > 0:
                        line_vals = {
                            'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'product_uom_qty': remaining_qty,
                            'price_unit': line.price_unit,
                            'tax_id': [(6,0,line.tax_id.ids)]
                        }
                        line.write({'sale_qty': line.sale_qty + remaining_qty})
                        line_data.append((0, 0, line_vals))
                    else:
                        raise UserError('Quantity not available!')
            if check_all_partial_count == 0:
                raise UserError('All quantity in request lines are partially available.')
            vals['order_line'] = line_data
        self.env['sale.order'].create(vals)
        sale_request.write({'state': 'partial', 'check_material_request_btn': True})

    def action_no(self):
        sale_request = self.env['sale.request'].browse(self._context.get('active_id'))
        vals = {}
        for record in sale_request:
            vals['partner_id'] = record.partner_id.id
            vals['sale_request_id'] = record.id
            vals['warehouse_id'] = record.warehouse_id.id
            vals['date_order'] = record.date_order
            vals['payment_term_id'] = record.payment_term_id.id
            line_data = []
            for line in record.request_line:
                qty_available = line.product_id.with_context({'warehouse': sale_request.warehouse_id.id}).qty_available
                final_qty = qty_available
                if line.product_uom_qty < qty_available:
                    final_qty = line.product_uom_qty
                line_vals = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_uom_qty': final_qty,
                    'price_unit': line.price_unit,
                    'tax_id': [(6,0,line.tax_id.ids)]
                }
                line.write({'sale_qty': final_qty})
                line_data.append((0, 0, line_vals))
            vals['order_line'] = line_data
        self.env['sale.order'].create(vals)
        sale_request.write({'state': 'done'})
