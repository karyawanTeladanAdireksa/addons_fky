
from odoo import api, fields, models, tools, _

class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    force_rate = fields.Float(string='Rate Amount', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    force_kurs_rate = fields.Float(digits=0,group_operator='avg',compute="_compute_force_kurs_rate")

    @api.onchange('journal_id', 'company_id', 'currency_id', 'payment_date')
    def _onchange_currency_rate(self):
        for payment in self:
            if not payment.journal_id:
                return
            company_currency = payment.company_id.currency_id
            payment_currency = payment.currency_id or company_currency
            if payment_currency != company_currency:
                payment.force_rate = payment_currency._convert(1.0, company_currency, payment.company_id, payment.date)
            else:
                payment.force_rate = 1.0

    @api.depends('currency_id','force_rate')
    def _compute_force_kurs_rate(self):
        last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(self.company_id | self.env.company)
        for line in self:
            if line.currency_id == self.env.company.currency_id:
                line.force_kurs_rate = 1.0
                continue
            company = line.company_id or self.env.company
            currenct_company_rate = 1.0 / (line.force_rate or 1.0)
            line.force_kurs_rate = currenct_company_rate * last_rate[company]

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        return super(AccountPayment, self.with_context(force_rate=self.force_kurs_rate))._prepare_move_line_default_vals(write_off_line_vals)
    