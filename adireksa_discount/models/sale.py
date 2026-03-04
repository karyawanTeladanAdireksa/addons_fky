from odoo import fields, models, api, _
from odoo.exceptions import UserError

import json


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total','diskon')
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        super(SaleOrder,self)._amount_all()
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            # order.amount_untaxed = sum(order_lines.mapped('price_subtotal'))
            # order.amount_tax = sum(order_lines.mapped('price_tax'))
            # order.amount_total = order.amount_untaxed + order.amount_tax
            amount_untaxed = order.amount_untaxed
            amount_tax = order.amount_tax
            amount_total = order.amount_total
            total_discount = discount_line_total = total_disc = 0.0
            for line in order_lines:
                total_discount += (line.product_uom_qty * line.price_unit - line.price_subtotal)
                discount_line_total += line.diskon_total 
            discount_details = []
            if order.diskon:
                disc_amt = amount_untaxed - total_discount
                amount_untaxed_deduct = amount_untaxed - total_discount
                count = 1
                for disc in order.diskon:
                    if len(order.diskon) > 1:
                        if count == 1:
                            disc_amt = amount_untaxed_deduct - (disc_amt * (1 - (disc.formula_diskon or 0.0) / 100.0))
                            discount_details.append((disc.name.split('(')[0].strip(), disc_amt))
                            total_disc += disc_amt
                            amount_untaxed_deduct = amount_untaxed_deduct - disc_amt
                            count += 1
                        else:
                            disc_amt = amount_untaxed_deduct - (amount_untaxed_deduct * (1 - (disc.formula_diskon or 0.0) / 100.0))
                            discount_details.append((disc.name.split('(')[0].strip(), disc_amt))
                            total_disc += disc_amt
                            amount_untaxed_deduct = amount_untaxed_deduct - disc_amt
                    else:
                        disc_amt = amount_untaxed_deduct - (disc_amt * (1 - (disc.formula_diskon or 0.0) / 100.0))
                        discount_details.append((disc.name.split('(')[0].strip(), disc_amt))
                        total_disc += disc_amt
                        amount_untaxed_deduct = amount_untaxed_deduct - disc_amt + amount_tax
            order.update({
                'discount_amount': total_disc + total_discount,
                'amount_total': amount_total - total_disc - total_discount,
                'discount_lines':discount_line_total,
            })
    # @api.depends('order_line.price_total', 'diskon')
    # def _amount_all(self):
    #     super(SaleOrder, self)._amount_all()
    #     for order in self:
    #         amount_untaxed = amount_tax = disc_amt = amount_untaxed_deduct = total_disc = 0.0
    #         discount_line_total = 0.0
    #         total_discount = 0.0
    #         for line in order.order_line:
    #             amount_untaxed += (line.product_uom_qty * line.price_unit)   #line.price_subtotal
    #             total_discount += (line.product_uom_qty * line.price_unit - line.price_subtotal)
    #             discount_line_total += line.diskon_total
    #             if order.company_id.tax_calculation_rounding_method == 'round_globally':
    #                 price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #                 taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
    #                 amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
    #             else:
    #                 amount_tax += line.price_tax

    #         discount_details = []
    #         if order.diskon:
    #             disc_amt = amount_untaxed - total_discount
    #             amount_untaxed_deduct = amount_untaxed - total_discount
    #             count = 1
    #             for disc in order.diskon:
    #                 if len(order.diskon) > 1:
    #                     if count == 1:
    #                         disc_amt = amount_untaxed_deduct - (disc_amt * (1 - (disc.formula_diskon or 0.0) / 100.0))
    #                         discount_details.append((disc.name.split('(')[0].strip(), disc_amt))
    #                         total_disc += disc_amt
    #                         amount_untaxed_deduct = amount_untaxed_deduct - disc_amt
    #                         count += 1
    #                     else:
    #                         disc_amt = amount_untaxed_deduct - (amount_untaxed_deduct * (1 - (disc.formula_diskon or 0.0) / 100.0))
    #                         discount_details.append((disc.name.split('(')[0].strip(), disc_amt))
    #                         total_disc += disc_amt
    #                         amount_untaxed_deduct = amount_untaxed_deduct - disc_amt
    #                 else:
    #                     disc_amt = amount_untaxed_deduct - (disc_amt * (1 - (disc.formula_diskon or 0.0) / 100.0))
    #                     discount_details.append((disc.name.split('(')[0].strip(), disc_amt))
    #                     total_disc += disc_amt
    #                     amount_untaxed_deduct = amount_untaxed_deduct - disc_amt + amount_tax

    #         order.update({
    #             'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
    #             'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
    #             'discount_amount': total_disc + total_discount,
    #             'amount_total': amount_untaxed - total_disc - total_discount + amount_tax,
    #             'discount_lines':discount_line_total,
    #         })
            # ir_values_obj = self.env['ir.values']
            # allow_credit = ir_values_obj.get_default('account.config.settings', 'allow_over_limit')
            # if allow_credit:
            #     if order.partner_id.credit_limit:
            #         credit_apprv_matrix_ids = self.env['credit.approving.matrix'].search([])
            #         for credit in credit_apprv_matrix_ids:
            #             for line in credit.credit_approving_matrix_ids:
            #                 if order.amount_total > line.min_amount and order.amount_total < line.max_amount:
            #                     order.update({
            #                         'credit_approving_matrix_id': credit.id
            #                         })
            #                 else:
            #                     order.update({
            #                         'credit_approving_matrix_id': False
            #                         })
            # order.multi_discount_info = json.dumps(False)
            # info = {'title': _('Multi Discount Info'), 'content': []}
            # for detail in discount_details:

            #     info['content'].append({
            #         'name': detail[0],
            #         'amount':detail[1],
            #         'digits': [69, order.company_id.currency_id.decimal_places],
            #         'position': order.company_id.currency_id.position,
            #         'currency': order.company_id.currency_id.symbol,
            #     })
            # order.multi_discount_info = json.dumps(info)

    diskon = fields.Many2many('adireksa.discount', string="Diskon")
    discount_amount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    kelas_customer = fields.Selection(
        [('blue', 'Blue (Annapurna)'),
         ('platinum', 'Platinum'),
         ('gold', 'Gold'),
         ('silver', 'Silver'),
         ('kelas_1_2', 'Kelas 2 & Kelas 1')],
        string='Kelas Customer')
    kelas_customer_id = fields.Many2one(
        'customer.class',
        string='Kelas Customer',
        related='partner_id.kelas_id'
    )
    # multi_discount_info = fields.Text(
    #     string='Multi Discount Info', compute='_compute_amounts', store=True
    # )

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     """
    #     Update the following fields when the partner is changed:
    #     - Pricelist
    #     - Payment term
    #     - Invoice address
    #     - Delivery address
    #     """

    #     if not self.partner_id:
    #         self.update({
    #             'partner_invoice_id': False,
    #             'partner_shipping_id': False,
    #             'payment_term_id': False,
    #             'fiscal_position_id': False,
    #         })
    #         return

    #     price_list_company_id = self.partner_id.property_product_pricelist.sudo().company_id
    #     if not price_list_company_id or (price_list_company_id == self.env.user.company_id):
    #         price_list_id = self.partner_id.property_product_pricelist.id
    #     else:
    #         price_list_id = self.env['product.pricelist'].search(
    #             [('company_id', 'in', (self.env.user.company_id.id, False))], limit=1)
    #         price_list_id = price_list_id and price_list_id.id or False

    #     addr = self.partner_id.address_get(['delivery', 'invoice'])
    #     values = {
    #         'pricelist_id': price_list_id,
    #         'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
    #         'partner_invoice_id': addr['invoice'],
    #         'partner_shipping_id': addr['delivery'],
    #     }

    #     if self.env.user.company_id.sale_note:
    #         values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

    #     if self.partner_id.user_id:
    #         values['user_id'] = False
    #     if self.partner_id.team_id:
    #         values['team_id'] = self.partner_id.team_id.id
    #     self.update(values)

    # def _prepare_invoice(self):
    #     """
    #     Prepare the dict of values to create the new invoice for a sales order. This method may be
    #     overridden to implement custom invoice generation (making sure to call super() to establish
    #     a clean extension chain).
    #     """
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
    #         'kelas_customer_id': self.kelas_customer_id.id,
    #     }
    #     if self.diskon:
    #         invoice_vals.update({'diskon_bool': True})
    #     return invoice_vals

    discount_lines = fields.Monetary(string='Discount Lines', store=True, compute='_compute_amounts')



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    diskon_ids = fields.Many2many('adireksa.discount', string="Discount (%)")
    diskon_total = fields.Monetary(string='Total Discount', compute='_compute_amount')

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','diskon_ids')
    def _compute_amount(self):
        super(SaleOrderLine,self)._compute_amount()
        for line in self:
            price = line.price_unit
            origin_price = price
            for discount_line in line.diskon_ids:
                price = price * (1 - (discount_line.formula_diskon or 0.0) / 100.0)
            taxes_totals = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            amount_untaxed = taxes_totals['total_excluded']
            amount_tax = sum(t.get('amount', 0.0) for t in taxes_totals.get('taxes', []))

            taxes_diskon = line.tax_id.compute_all(origin_price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            amount_untaxed_diskon = taxes_diskon['total_excluded']
            amount_tax_diskon = sum(t.get('amount', 0.0) for t in taxes_diskon.get('taxes', []))
            line.update({
                'diskon_total': (amount_untaxed_diskon + amount_tax_diskon)  - \
                                    (amount_untaxed + amount_tax)
            })

    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'diskon_ids')
    # def _compute_amount(self):
    #     for line in self:
    #         price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #         original_amount = price
    #         # print "original_amount", original_amount
    #         for diskon_line in line.diskon_ids:
    #             price = price * (1 - (diskon_line.formula_diskon or 0.0) / 100.0)
    #         taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
    #                                         product=line.product_id, partner=line.order_id.partner_shipping_id)
    #         taxes_diskon = line.tax_id.compute_all(original_amount, line.order_id.currency_id, line.product_uom_qty,
    #                                         product=line.product_id, partner=line.order_id.partner_shipping_id)
    #         line.update({
    #             'price_tax': taxes['total_included'] - taxes['total_excluded'],
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #             'diskon_total': taxes_diskon['total_excluded'] - taxes['total_excluded']
    #         })

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        result = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        result['diskon_ids'] = [(6, 0, self.diskon_ids.ids)]
        return result

