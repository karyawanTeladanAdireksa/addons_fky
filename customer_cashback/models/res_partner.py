# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    cashback_generate = fields.Selection([('auto', 'Auto'), ('manual', 'Manual')], default='auto', string='Cashback Generate')
    type_omset = fields.Selection([('fixed', 'Fixed'), ('periodic', 'Periodic')], default='fixed', string='Type Omset')
    value_omset = fields.Float(string='Value Omset')
    omset_ids = fields.One2many('res.partner.omset', 'partner_id', string='End Date')
    get_cashback = fields.Boolean(string='Get Cashback')
    edit_cashback = fields.Boolean(string='Allow Edit Cashback')


class ResPartnerOmset(models.Model):
    _name = "res.partner.omset"

    value_omset = fields.Float(string='Value Omset')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    partner_id = fields.Many2one('res.partner')
