# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError,ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    
    # def _prepare_invoice(self):
    #     # Override this function fix the cashback value and discount value
    #     self.ensure_one()
    #     journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
    #     if not journal_id:
    #         raise UserError(_('Please define an accounting sale journal for this company.'))
    #     invoice_vals = {
    #         'name': self.client_order_ref or '',
    #         'origin': self.name,
    #         'type': 'out_invoice',
    #         'reference': self.client_order_ref or self.name,
    #         'account_id': self.partner_invoice_id.property_account_receivable_id.id,
    #         'partner_id': self.partner_invoice_id.id,
    #         'journal_id': journal_id,
    #         'branch_id': self.branch_id.id,
    #         'currency_id': self.pricelist_id.currency_id.id,
    #         'comment': self.note,
    #         'payment_term_id': self.payment_term_id.id,
    #         'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
    #         'company_id': self.company_id.id,
    #         'user_id': self.user_id and self.user_id.id,
    #         'team_id': self.team_id.id,
    #         'diskon': [(6, 0, self.diskon.ids)],
    #         'kelas_customer': self.kelas_customer,
    #         'kelas_customer_id': self.kelas_customer_id.id,
    #         'cashback_id': [(6, 0, self.cashback_id.ids)],
    #     }
    #     if self.diskon:
    #         invoice_vals.update({'diskon_bool': True})
    #     if self.cashback_id:
    #         invoice_vals.update({'cashback_bool': True})
    #     return invoice_vals


# class SaleRequest(models.Model):
#     _inherit = 'sale.request'

#     def action_create_sale_order(self):
#         # Override
#         if self.state == "partial":
#             warning_txt = 'This Sales Request still has an Outstanding item product. Do you want to do Backorder for outstanding item?'
#             return {
#                 'name': 'Warning',
#                 'type': 'ir.actions.act_window',
#                 'res_model': 'sr.message',
#                 'view_type': 'form',
#                 'view_mode': 'form',
#                 'target': 'new',
#                 'context': {'default_message': warning_txt}
#             }
#         elif self.state == "available":
#             vals = {}
#             vals['partner_id'] = self.partner_id.id
#             vals['sale_request_id'] = self.id
#             vals['warehouse_id'] = self.warehouse_id.id
#             vals['date_order'] = self.date_order
#             vals['payment_term_id'] = self.payment_term_id.id
#             line_data = []
#             for line in self.request_line:
#                 quotation_ids = self.env['sale.order'].search([('sale_request_id', '=', self.id)])
#                 if quotation_ids:
#                     lines_ids = quotation_ids.mapped('order_line').filtered(lambda a: a.product_id == line.product_id)
#                     product_uom_qty = sum(lines_ids.mapped('product_uom_qty'))
#                     qty_available = line.product_id.with_context({'warehouse': self.warehouse_id.id}).qty_available
#                     remaining_qty = qty_available - product_uom_qty
#                     check_all_partial_count = 1
#                     if line.product_uom_qty != line.sale_qty and remaining_qty > 0:
#                         line_vals = {
#                             'product_id': line.product_id.id,
#                             'name': line.product_id.name,
#                             'product_uom_qty': remaining_qty,
#                             'price_unit': line.price_unit,
#                             'tax_id': [(6,0,line.tax_id.ids)]
#                         }
#                         line.write({'sale_qty': line.sale_qty + remaining_qty})
#                         line_data.append((0, 0, line_vals))
#                 else:
#                     line_vals = {}
#                     if line.product_uom_qty - line.sale_qty > 0:
#                         line_vals['product_id'] = line.product_id.id
#                         line_vals['name'] = line.product_id.name
#                         line_vals['product_uom_qty'] = line.product_uom_qty
#                         line_vals['price_unit'] = line.price_unit
#                         line_vals['tax_id'] = [(6, 0, line.tax_id.ids)]
#                         line.write({'sale_qty': line.product_uom_qty})
#                         line_data.append((0, 0, line_vals))
#             vals['order_line'] = line_data
#             self.env['sale.order'].create(vals)
#             self.write({'state': 'done'})
#         else:
#             vals = {}
#             vals['partner_id'] = self.partner_id.id
#             vals['sale_request_id'] = self.id
#             vals['warehouse_id'] = self.warehouse_id.id
#             vals['date_order'] = self.date_order
#             vals['payment_term_id'] = self.payment_term_id
#             vals['kelas_customer'] = self.partner_id.kelas
#             vals['kelas_customer_id'] = self.partner_id.kelas_id
#             line_data = []
#             for line in self.request_line:
#                 line_vals = {}
#                 line_vals['product_id'] = line.product_id.id
#                 line_vals['name'] = line.product_id.name
#                 line_vals['product_uom_qty'] = line.product_uom_qty
#                 line_vals['price_unit'] = line.price_unit
#                 line_vals['qty_delivered'] = line.qty_delivered
#                 line_vals['qty_invoiced'] = line.qty_invoiced
#                 line_data.append((0, 0, line_vals))
#             vals['order_line'] = line_data
#             self.env['sale.order'].create(vals)
#             self.write({'state': 'quotation'})
