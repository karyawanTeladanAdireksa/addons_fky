from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"


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
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        super(AccountMove,self)._compute_amount()
        for move in self:
            disc_amt = amount_untaxed_deduct = total_currency = total  = amount_untaxed = amount_tax = total_disc = cashback_amt = 0.0
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
            if move.cashback_id:
                percent = 0.0
                amount_total_b_cashback = amount_untaxed - total_disc + amount_tax
                for cb in move.cashback_id:
                    if len(move.cashback_id) > 1:
                        percent += cb.cashback_formula
                    else:
                        percent = cb.cashback_formula
                cashback_amt = amount_total_b_cashback - (amount_total_b_cashback * (1 - (percent or 0.0) / 100.0))

                move.amount_total_before_cashback = amount_untaxed - move.discount_amount + amount_tax
                move.cashback_amount = cashback_amt
                move.amount_total -= cashback_amt


    cashback_id = fields.Many2many('adireksa.cashback', string="Cashback")
    cashback_bool = fields.Boolean(string="Cashback Bool")
    amount_total_before_cashback = fields.Monetary(string='Amount Total Before Cashback',
                                   store=True, readonly=True, compute='_compute_amount')
    cashback_amount = fields.Monetary(string='Cashback Amount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')
