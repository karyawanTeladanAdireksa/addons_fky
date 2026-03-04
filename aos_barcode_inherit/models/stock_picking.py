# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.tools import html2plaintext, is_html_empty


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def action_print_delivery_slip(self):
        return self.env.ref('adireksa_do_slip.action_report_delivery_order').report_action(self)