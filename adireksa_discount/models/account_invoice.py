from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'diskon', 
        'discount_amount')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for move in self:
            disc_amt = amount_untaxed_deduct = total_disc = amount_untaxed = total = amount_tax = total_currency = 0.0
            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            for line in move.line_ids:
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        amount_tax += line.amount_currency
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        amount_untaxed += line.amount_currency
                        total_currency += line.amount_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency
            amount_untaxed = sign * amount_untaxed
            amount_tax = sign * amount_tax
            if move.diskon:
                disc_amt = amount_untaxed
                amount_untaxed_deduct = amount_untaxed
                count = 1
                for disc in move.diskon:
                    if len(move.diskon) > 1:
                        if count == 1:
                            disc_amt = amount_untaxed_deduct - (disc_amt * (1 - (disc.formula_diskon or 0.0) / 100.0))
                            total_disc += disc_amt
                            amount_untaxed_deduct = amount_untaxed_deduct - disc_amt
                            count += 1
                        else:
                            disc_amt = amount_untaxed_deduct - (
                                        amount_untaxed_deduct * (1 - (disc.formula_diskon or 0.0) / 100.0))
                            total_disc += disc_amt
                            amount_untaxed_deduct = amount_untaxed_deduct - disc_amt
                    else:
                        disc_amt = amount_untaxed_deduct - (disc_amt * (1 - (disc.formula_diskon or 0.0) / 100.0))
                        total_disc += disc_amt
                        amount_untaxed_deduct = amount_untaxed_deduct - disc_amt + amount_tax

            move.amount_total = move.amount_total - total_disc
            move.discount_amount = total_disc

    diskon = fields.Many2many('adireksa.discount', string="Diskon")
    diskon_bool = fields.Boolean(string="Diskon Bool")
    discount_amount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')
    kelas_customer = fields.Selection(
        [('blue', 'Blue (Annapurna)'),
         ('platinum', 'Platinum'),
         ('gold', 'Gold'),
         ('silver', 'Silver'),
         ('kelas_1_2', 'Kelas Umum')],
        string='Kelas Customer')
    kelas_customer_id = fields.Many2one(
        'customer.class',
        string='Kelas Customer',
    )

    # @api.onchange('partner_id', 'company_id')
    # def _onchange_partner_id(self):
    #     account_id = False
    #     payment_term_id = False
    #     fiscal_position = False
    #     bank_id = False
    #     warning = {}
    #     domain = {}
    #     company_id = self.company_id.id
    #     p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
    #     type = self.type
    #     if p:
    #         rec_account = p.property_account_receivable_id
    #         pay_account = p.property_account_payable_id
    #         if not rec_account and not pay_account:
    #             action = self.env.ref('account.action_account_config')
    #             msg = _(
    #                 'Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
    #             raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

    #         if type in ('in_invoice', 'in_refund'):
    #             account_id = pay_account.id
    #             payment_term_id = p.property_supplier_payment_term_id.id
    #         else:
    #             account_id = rec_account.id
    #             payment_term_id = p.property_payment_term_id.id

    #         delivery_partner_id = self.get_delivery_partner_id()
    #         fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id,
    #                                                                                   delivery_id=delivery_partner_id)

    #         # If partner has no warning, check its company
    #         if p.invoice_warn == 'no-message' and p.parent_id:
    #             p = p.parent_id
    #         if p.invoice_warn != 'no-message':
    #             # Block if partner only has warning but parent company is blocked
    #             if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
    #                 p = p.parent_id
    #             warning = {
    #                 'title': _("Warning for %s") % p.name,
    #                 'message': p.invoice_warn_msg
    #             }
    #             if p.invoice_warn == 'block':
    #                 self.partner_id = False

    #     self.account_id = account_id
    #     self.payment_term_id = payment_term_id
    #     self.date_due = False
    #     self.fiscal_position_id = fiscal_position
    #     self.kelas_customer_id = p.kelas_id

    #     if type in ('in_invoice', 'out_refund'):
    #         bank_ids = p.commercial_partner_id.bank_ids
    #         bank_id = bank_ids[0].id if bank_ids else False
    #         self.partner_bank_id = bank_id
    #         domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}

    #     res = {}
    #     if warning:
    #         res['warning'] = warning
    #     if domain:
    #         res['domain'] = domain
    #     return res

    # def compute_invoice_totals(self, company_currency, invoice_move_lines):
    #     if self.discount_amount:
    #         disc = self.discount_amount or 0.0
    #         for line in invoice_move_lines:
    #             line['price'] -= disc
    #             break

    #     return super(AccountInvoice, self).compute_invoice_totals(company_currency, invoice_move_lines)

    discount_lines = fields.Monetary(string='Discount Lines', store=True, compute='_compute_amount')

    @api.onchange('shipment_ids')
    def shipment_ids_change(self):
        if self.shipment_ids:
            self.diskon_bool = True
        else:
            self.diskon_bool = False


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    diskon_ids = fields.Many2many('adireksa.discount', string="Diskon (%)")
    diskon_total = fields.Monetary(string='Diskon Total', compute='_compute_totals')

    # @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
    #              'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
    #              'invoice_id.date_invoice', 'invoice_id.date', 'diskon_ids')
    # def _compute_price(self):
    #     for line in self:
    #         currency = line.move_id and line.move_id.currency_id or None
    #         price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #         original_amount = price
    #         taxes = False
    #         for diskon_line in line.diskon_ids:
    #             price = price * (1 - (diskon_line.formula_diskon or 0.0) / 100.0)
    #         taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id,
    #                                                         partner=line.invoice_id.partner_id)
    #         taxes_diskon = line.invoice_line_tax_ids.compute_all(original_amount, currency, line.quantity, product=line.product_id,
    #                                                     partner=line.invoice_id.partner_id)
    #         line.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else line.quantity * price
    #         line.diskon_total = taxes_diskon['total_excluded'] - taxes['total_excluded']
    #         if line.invoice_id.currency_id and line.invoice_id.company_id and line.invoice_id.currency_id != line.invoice_id.company_id.currency_id:
    #             price_subtotal_signed = line.invoice_id.currency_id.with_context(
    #                 date=line.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
    #                                                                         line.invoice_id.company_id.currency_id)
    #         sign = line.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
    #         line.price_subtotal_signed = price_subtotal_signed * sign

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            if line.display_type != 'product':
                line.price_total = line.price_subtotal = False
            # Compute 'price_subtotal'.
            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            original_amount =line_discount_price_unit
            for discount_line in line.diskon_ids:
                line_discount_price_unit = line_discount_price_unit * (1 - (discount_line.formula_diskon / 100.0))
            subtotal = line.quantity * line_discount_price_unit

            # Compute 'price_total'.
            taxes_diskon = line.tax_ids.compute_all(original_amount, line.currency_id, line.quantity, product=line.product_id,
                                                        partner=line.move_id.partner_id,is_refund=line.move_id.move_type in ('out_refund','in_refund'))
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.move_id.move_type in ('out_refund','in_refund'),
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
                line.diskon_total = taxes_diskon['total_excluded'] - taxes_res['total_excluded']
            else:
                line.price_total = line.price_subtotal = subtotal
                line.diskon_total = taxes_diskon['total_excluded'] - taxes_diskon['total_included']