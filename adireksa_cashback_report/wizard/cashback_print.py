# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta


class CashbackPrint(models.TransientModel):
    _name = "cashback.print"
    _description = "Cashback Print"

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date') 
    previous_balance = fields.Float(string="Previous Balance",compute="_compute_previous_balance")

    @api.depends('date_from','date_to')
    def _compute_previous_balance(self):
        for rec in self :
            rec.previous_balance = 0
            mcc_id = self.env['master.customer.cashback'].browse(self._context.get('active_id'))
            if rec.date_from and rec.date_to:
                # mcc_lines_debit = sum(mcc_id.line_ids.filtered(lambda x:x.date >= rec.date_from and x.date <= rec.date_to and x.state == 'approve' and x.default_posting == 'debit').mapped('value'))
                # mcc_lines_credit = sum(mcc_id.line_ids.filtered(lambda x:x.date >= rec.date_from and x.date <= rec.date_to and x.state == 'approve' and x.default_posting == 'credit').mapped('value'))
                prev_mcc_lines_debit = sum(mcc_id.line_ids.filtered(lambda x:x.date < rec.date_from and x.state == 'approve' and x.default_posting == 'debit').mapped('value'))
                prev_mcc_lines_credit = sum(mcc_id.line_ids.filtered(lambda x:x.date < rec.date_from and x.state == 'approve' and x.default_posting == 'credit').mapped('value'))
                rec.previous_balance = prev_mcc_lines_debit - prev_mcc_lines_credit

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['previous_balance'] = data['form']['previous_balance'] or False
        return result 

    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'master.customer.cashback')
        data['form'] = self.read(['date_from', 'date_to','previous_balance'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self.env.ref('adireksa_cashback_report.action_report_cashback').report_action(self.ids, data=data)


# class MasterCustomerCashback(models.Model):
#     _inherit = 'master.customer.cashback'

#     def print_cashback_report(self):
#         view = self.env.ref('adireksa_cashback_report.cashback')
#         return {
#             'name': ('Print Cashback Report'),
#             'type': 'ir.actions.act_window',
#             'view_mode': 'form',
#             'res_model': 'cashback.print',
#             'views': [(view.id, 'form')],
#             'view_id': view.id,
#             'target': 'new',
#         }
