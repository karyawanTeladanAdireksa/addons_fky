# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

# class AccountBankStatementLine(models.Model):
#     _inherit = "account.bank.statement.line"
#     _description = "Bank Statement Line"
#     
#     force_rate = fields.Float('Rate Amount', compute='_get_currency_rate', store=True)
#     
#     @api.depends('partner_id', 'currency_id', 'date')
#     def _get_currency_rate(self):
#         for statement in self:
#             company_currency = statement.company_id.currency_id
#             statement_currency = statement.currency_id or company_currency
#             if statement_currency != company_currency:
#                 statement.force_rate = statement_currency.with_context(partner_id=statement.partner_id.id,date=statement.date).compute(1.0, company_currency, round=False)
#             else:
#                 statement.force_rate = 1.0
#                 
#     def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
#         counterpart_moves = super(AccountBankStatementLine, self.with_context(force_rate=self.force_rate)).process_reconciliation(counterpart_aml_dicts=counterpart_aml_dicts, payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
#         return counterpart_moves
# 
#     
#     def _prepare_move_line_for_currency(self, aml_dict, date):
#         vals = super(AccountBankStatementLine, self.with_context(force_rate=self.force_rate))._prepare_move_line_for_currency(aml_dict=aml_dict, date=date)
#         return vals
    