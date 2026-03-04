# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta


class CashbackPrint(models.TransientModel):
    _name = "cashback.print"
    _description = "Cashback Print"

    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    def _build_contexts(self, data):
        result = {}
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        return result

    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self.env['report'].get_action(self, 'adireksa_cashback_pattern.report_cashback_new', data=data)
