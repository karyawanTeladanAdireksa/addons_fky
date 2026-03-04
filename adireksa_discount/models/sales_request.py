from odoo import models, fields, api


class SaleRequest(models.Model):
    _inherit = "sale.request"

    
    def action_create_sale_order(self):
        if self.state == "partial":
            warning_txt = 'This Sales Request still has an Outstanding item product. Do you want to do Backorder for outstanding item?'
            return {
                'name': 'Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'sr.message',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_message': warning_txt}
            }
        elif self.state == "available":
            vals = {}
            vals['partner_id'] = self.partner_id.id
            vals['sale_request_id'] = self.id
            vals['warehouse_id'] = self.warehouse_id.id
            vals['date_order'] = self.date_order
            vals['payment_term_id'] = self.payment_term_id.id
            line_data = []
            for line in self.request_line:
                quotation_ids = self.env['sale.order'].search([('sale_request_id', '=', self.id)])
                if quotation_ids:
                    lines_ids = quotation_ids.mapped('order_line').filtered(lambda a: a.product_id == line.product_id)
                    product_uom_qty = sum(lines_ids.mapped('product_uom_qty'))
                    qty_available = line.product_id.with_context({'warehouse': self.warehouse_id.id}).qty_available
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
                    line_vals = {}
                    if line.product_uom_qty - line.sale_qty > 0:
                        line_vals['product_id'] = line.product_id.id
                        line_vals['name'] = line.product_id.name
                        line_vals['product_uom_qty'] = line.product_uom_qty
                        line_vals['price_unit'] = line.price_unit
                        line_vals['tax_id'] = [(6, 0, line.tax_id.ids)]
                        line.write({'sale_qty': line.product_uom_qty})
                        line_data.append((0, 0, line_vals))
            vals['order_line'] = line_data
            self.env['sale.order'].create(vals)
            self.write({'state': 'done'})
        else:
            vals = {}
            vals['partner_id'] = self.partner_id.id
            vals['sale_request_id'] = self.id
            vals['warehouse_id'] = self.warehouse_id.id
            vals['date_order'] = self.date_order
            vals['payment_term_id'] = self.payment_term_id
            vals['kelas_customer'] = self.partner_id.kelas
            line_data = []
            for line in self.request_line:
                line_vals = {}
                line_vals['product_id'] = line.product_id.id
                line_vals['name'] = line.product_id.name
                line_vals['product_uom_qty'] = line.product_uom_qty
                line_vals['price_unit'] = line.price_unit
                line_vals['qty_delivered'] = line.qty_delivered
                line_vals['qty_invoiced'] = line.qty_invoiced
                line_data.append((0, 0, line_vals))
            vals['order_line'] = line_data
            self.env['sale.order'].create(vals)
            self.write({'state': 'quotation'})