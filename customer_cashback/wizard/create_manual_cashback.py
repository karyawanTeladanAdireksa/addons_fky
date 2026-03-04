# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import ValidationError


class CreateCashbackLines(models.TransientModel):

    _name = 'create.cashback.lines'
    _description = 'Create Cashback Lines'

    @api.model
    def _get_cashback_id(self):
        cashback_id = self.env.context.get('active_id', False)
        return cashback_id

    date = fields.Date('Date')
    type_id = fields.Many2one('cashback.type', 'Type')
    reference = fields.Char('Reference')
    state = fields.Selection([('draft', 'Draft'), ('waiting_for_approval', 'Waiting Approval'), ('approve', 'Approve')], default='draft', string='Status', readonly=True, copy=False, index=True)
    user_id = fields.Many2one('res.users', string='Add By', default=lambda self: self.env.user)
    cashback_id = fields.Many2one('master.customer.cashback', default=_get_cashback_id)
    line_ids = fields.One2many('create.cashback.so.lines', 'create_cashback_id')

    start_date = fields.Date('Start Date', default=datetime.now().strftime('%Y-%m-01'))
    end_date = fields.Date('End Date', default=datetime.now().strftime('%Y-%m-01'))
    real_omset = fields.Float('Real Omset', compute="compute_real_omset")
    total_omset = fields.Float('Total Omset', compute="compute_total_omset")
    final_omset = fields.Float('Final Omset', compute="compute_final_omset")
    cashback = fields.Float('Cashback %')
    cashback_calculation = fields.Boolean('Cashback Calculation')
    value = fields.Float('Value')

    @api.onchange('cashback', 'final_omset')
    def onchange_cashback(self):
        for res in self:
            res.value = res.final_omset * res.cashback / 100


    @api.depends('line_ids.so_value', 'cashback_calculation')
    def compute_real_omset(self):
        for res in self:
            if res.cashback_calculation:
                res.real_omset = sum([line.so_value for line in res.line_ids])

    @api.depends('real_omset', 'total_omset', 'cashback_calculation')
    def compute_final_omset(self):
        for res in self:
            if res.cashback_calculation:
                final_omset = res.real_omset - res.total_omset
                if final_omset < 0:
                    final_omset = 0
                res.final_omset = final_omset

    @api.depends('real_omset', 'start_date', 'end_date', 'cashback_calculation')
    def compute_total_omset(self):
        for res in self:
            if res.cashback_calculation and res.start_date and res.end_date:
                date1 = datetime.strptime(res.start_date, '%Y-%m-%d')
                date2 = datetime.strptime(res.end_date, '%Y-%m-%d')
                r = relativedelta.relativedelta(date2, date1)
                month = (r.months + (12*r.years)) + 1
                value_omset = 0.0
                date_domain = [('end_date', '>', res.start_date), ('start_date', '<', res.end_date),
                          '|', ('start_date', '>=', res.start_date), ('start_date', '<=', res.start_date),
                          '|', ('end_date', '>=', res.end_date), ('end_date', '<=', res.end_date)] 
                if 'partner_id' in self._context and self._context.get('partner_id'):
                    partner_id = self.env['res.partner'].browse(self._context.get('partner_id'))
                    if partner_id.type_omset == 'fixed':
                        value_omset = partner_id.value_omset * month
                    else:
                        omset = self.env['res.partner.omset'].search([('partner_id', '=', partner_id.id)] + date_domain)
                        value_omset += sum([om.value_omset for om in omset])
                if 'group_id' in self._context and self._context.get('group_id'):
                    partner_id = self.env['res.partner'].search([('category_id', '=', self._context.get('group_id'))])
                    value_omset += (sum([part.value_omset for part in partner_id.filtered(lambda x: x.type_omset == 'fixed')])) * month
                    omset = self.env['res.partner.omset'].search([('partner_id', 'in', partner_id.ids)] + date_domain)
                    value_omset += sum([om.value_omset for om in omset])
                res.total_omset = value_omset

    @api.onchange('start_date', 'end_date')
    def onchange_start_end_date(self):
        if self.start_date or self.end_date:
            self.line_ids = False
            partner_id = self._context.get('partner_id') if 'partner_id' in self._context else False
            group_id = self._context.get('group_id') if 'group_id' in self._context else False
            if partner_id:
                partner_id = self.env['res.partner'].browse(partner_id)
            if group_id:
                partner_id = self.env['res.partner'].search([('category_id', '=', group_id)])
            qurstr = """SELECT id FROM sale_order WHERE confirmation_date BETWEEN '%s' AND '%s' AND state IN ('sale', 'lock')""" % (self.start_date, self.end_date)
            if partner_id:
                qurstr += """AND partner_id IN (%s)""" % ','.join(map(str,
                                                            partner_id.ids))
            self._cr.execute(qurstr)
            sale_ids = [sale[0] for sale in self._cr.fetchall()]
            sales_ids = self.env['sale.order'].browse(sale_ids)
            data = []
            for sale in sales_ids:
                data.append((0, 0, {
                        'so_id': sale.id,
                        'so_id': sale.id,
                        'so_date': sale.confirmation_date,
                        'so_value': sale.amount_total
                    }))
            self.line_ids = data


    def create_manual_cashback(self):
        if self.value == 0:
            raise ValidationError(_("Value is 0 !"))
        data = []
        for line in self.line_ids:
            data.append((0, 0, {
                    'so_id': line.so_id.id,
                    'so_date': line.so_date,
                    'so_value': line.so_value,
                }))
        self.env['manual.cashback.lines'].create({'date': self.date,
                     'type_id': self.type_id.id,
                     'value': self.value,
                     'reference': self.reference,
                     'cashback_id': self.cashback_id.id,
                     'start_date': self.start_date,
                     'end_date': self.end_date,
                     'real_omset': self.real_omset,
                     'total_omset': self.total_omset,
                     'final_omset': self.final_omset,
                     'cashback': self.cashback,
                     'value': self.value,
                     'line_ids': data,
                     'cashback_calculation': self.cashback_calculation
                     })
        self.cashback_id.cashback_in += self.value
        return True


class CreateCashbackSOLines(models.TransientModel):

    _name = 'create.cashback.so.lines'
    _description = 'Create Cashback SO Lines'

    so_id = fields.Many2one('sale.order', 'SO Number')
    so_date = fields.Date('SO Date')
    so_value = fields.Float('SO Value')
    create_cashback_id = fields.Many2one('create.cashback.lines')