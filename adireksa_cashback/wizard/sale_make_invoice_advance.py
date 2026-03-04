# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    cashback_id = fields.Many2many('adireksa.cashback', string="Cashback")

    # @api.onchange('cashback_id')
    # def onchange_cashback_id(self):
    #     # customer_omset = self.env['adireksa.omset']
    #     # customer_omset_line = self.env['omset.lines']
    #     customer_cashback = self.env['adireksa.cashback']
    #     invoice = self.env['account.move']
    #     sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
    #     total = 0.0
    #     cashback_lst = []
    #     for sale in sale_orders:
    #         if sale.partner_id:
    #             omset_line_ids = customer_omset_line.search([('partner_id', '=', sale.partner_id.id), ('aktifkan_omset', '=', True)])
    #             if omset_line_ids:
    #                 for omset_line in customer_omset_line.search([('partner_id', '=', sale.partner_id.id), ('aktifkan_omset', '=', True)]):
    #                     cashback_ids = customer_cashback.search([('kelas_customer', '=', sale.partner_id.kelas), ('aktifkan_cashback', '=', True),
    #                                                              ('jenis_omset', '=', omset_line.jenis_omset)])
    #                     if cashback_ids:
    #                         for cashback in customer_cashback.search([('kelas_customer', '=', sale.partner_id.kelas), ('aktifkan_cashback', '=', True),
    #                                                              ('jenis_omset', '=', omset_line.jenis_omset), ('state', '=', 'approved')]):
    #                             invoice_ids = invoice.search([('partner_id', '=', sale.partner_id.id), ('payment_state', '=', 'paid'),
    #                                         ('invoice_date', '>=', cashback.period_start), ('invoice_date', '<=', cashback.period_end)])
    #                             if invoice_ids:
    #                                 for inv in invoice.search([('partner_id', '=', sale.partner_id.id), ('payment_state', '=', 'paid'),
    #                                         ('invoice_date', '>=', cashback.period_start), ('invoice_date', '<=', cashback.period_end)]):
    #                                     total += inv.amount_total
    #                             if omset_line.target_omset <= total:
    #                                 cashback_lst.append(cashback.id)
                    # return {'domain': {'cashback_id': [('id', 'in', cashback_lst)]}}

    
    # def _create_invoice(self, order, so_line, amount):
    #     print("IS THIS CALLED while cashabck _create_invoice")
    #     inv_obj = self.env['account.invoice']
    #     ir_property_obj = self.env['ir.property']

    #     account_id = False
    #     if self.product_id.id:
    #         account_id = self.product_id.property_account_income_id.id or self.product_id.categ_id.property_account_income_categ_id.id
    #     if not account_id:
    #         inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
    #         account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
    #     if not account_id:
    #         raise UserError(
    #             _(
    #                 'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
    #             (self.product_id.name,))

    #     if self.amount <= 0.00:
    #         raise UserError(_('The value of the down payment amount must be positive.'))
    #     context = {'lang': order.partner_id.lang}
    #     if self.advance_payment_method == 'percentage':
    #         amount = order.amount_untaxed * self.amount / 100
    #         name = _("Down payment of %s%%") % (self.amount,)
    #     else:
    #         amount = self.amount
    #         name = _('Down Payment')
    #     del context
    #     taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
    #     if order.fiscal_position_id and taxes:
    #         tax_ids = order.fiscal_position_id.map_tax(taxes).ids
    #     else:
    #         tax_ids = taxes.ids

    #     invoice = inv_obj.create({
    #         'name': order.client_order_ref or order.name,
    #         'origin': order.name,
    #         'type': 'out_invoice',
    #         'reference': False,
    #         'account_id': order.partner_id.property_account_receivable_id.id,
    #         'partner_id': order.partner_invoice_id.id,
    #         'partner_shipping_id': order.partner_shipping_id.id,
    #         'invoice_line_ids': [(0, 0, {
    #             'name': name,
    #             'origin': order.name,
    #             'account_id': account_id,
    #             'price_unit': amount,
    #             'quantity': 1.0,
    #             'discount': 0.0,
    #             'uom_id': self.product_id.uom_id.id,
    #             'product_id': self.product_id.id,
    #             'sale_line_ids': [(6, 0, [so_line.id])],
    #             'invoice_line_tax_ids': [(6, 0, tax_ids)],
    #             'diskon_ids': [(6, 0, so_line.diskon_ids.ids)],
    #             'account_analytic_id': order.project_id.id or False,
    #         })],
    #         'currency_id': order.pricelist_id.currency_id.id,
    #         'payment_term_id': order.payment_term_id.id,
    #         'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
    #         'team_id': order.team_id.id,
    #         'user_id': order.user_id.id,
    #         'comment': order.note,
    #         'diskon': [(6, 0, [order.diskon.id])] if order.diskon else False,
    #         'kelas_customer': order.kelas_customer,
    #         'cashback_id': [(6, 0, [self.cashback_id.id])],
    #     })
    #     if order.diskon:
    #         invoice.update({'diskon_bool': True})
    #     if order.cashback_id:
    #         invoice.update({'cashback_bool': True})
    #     invoice.compute_taxes()
    #     invoice.message_post_with_view('mail.message_origin_link',
    #                                    values={'self': invoice, 'origin': order},
    #                                    subtype_id=self.env.ref('mail.mt_note').id)
    #     return invoice

    
    # def create_invoices(self):
    #     sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

    #     if sale_orders:
    #         if self.cashback_id:
    #             sale_orders.write({'cashback_id': [(6, 0, [self.cashback_id.id])]})

    #     if self.advance_payment_method == 'delivered':
    #         sale_orders.action_invoice_create()
    #     elif self.advance_payment_method == 'all':
    #         sale_orders.action_invoice_create(final=True)
    #     else:
    #         # Create deposit product if necessary
    #         if not self.product_id:
    #             vals = self._prepare_deposit_product()
    #             self.product_id = self.env['product.product'].create(vals)
    #             self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting',
    #                                                      self.product_id.id)

    #         sale_line_obj = self.env['sale.order.line']
    #         for order in sale_orders:
    #             if self.advance_payment_method == 'percentage':
    #                 amount = order.amount_untaxed * self.amount / 100
    #             else:
    #                 amount = self.amount
    #             if self.product_id.invoice_policy != 'order':
    #                 raise UserError(_(
    #                     'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
    #             if self.product_id.type != 'service':
    #                 raise UserError(_(
    #                     "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
    #             taxes = self.product_id.taxes_id.filtered(
    #                 lambda r: not order.company_id or r.company_id == order.company_id)
    #             if order.fiscal_position_id and taxes:
    #                 tax_ids = order.fiscal_position_id.map_tax(taxes).ids
    #             else:
    #                 tax_ids = taxes.ids
    #             context = {'lang': order.partner_id.lang}
    #             so_line = sale_line_obj.create({
    #                 'name': _('Advance: %s') % (time.strftime('%m %Y'),),
    #                 'price_unit': amount,
    #                 'product_uom_qty': 0.0,
    #                 'order_id': order.id,
    #                 'discount': 0.0,
    #                 'product_uom': self.product_id.uom_id.id,
    #                 'product_id': self.product_id.id,
    #                 'tax_id': [(6, 0, tax_ids)],
    #             })
    #             del context
    #             self._create_invoice(order, so_line, amount)
    #     if self._context.get('open_invoices', False):
    #         return sale_orders.action_view_invoice()
    #     return {'type': 'ir.actions.act_window_close'}
