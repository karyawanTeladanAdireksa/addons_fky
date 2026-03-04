from odoo import fields, models, api, _


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cashback_credit_id = fields.Many2one('account.account', string='Cashback Credit',
                                            config_parameter='adireksa_cashback_manual.cashback_credit_id')
    cashback_debit_id = fields.Many2one('account.account', string='Cashback Debit',
                                            config_parameter='adireksa_cashback_manual.cashback_debit_id')
    cashback_journal_id = fields.Many2one('account.journal', string='Journal Cashback', 
                                            config_parameter='adireksa_cashback_manual.cashback_journal_id')


