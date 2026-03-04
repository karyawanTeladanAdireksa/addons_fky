from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class WizardCashbackManual(models.TransientModel):
    _name = 'cashback.manual.wizard'
    _description = 'Cashback Manual Wizard'

    name = fields.Char(string="Name")
    memo = fields.Char(string="memo")
    amount_total = fields.Float(string="Amount Total")


    def btn_cashback_manual(self):
        form = self.env.ref('aos_cashback.view_cashback_manual_form')
        context = dict(self.env.context or {})
        view = {
            'name': "Manual Cashback",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cashback.manual',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new'
        }
        return view