# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import math
import calendar


class CustomerTarget(models.Model):
    _name = 'adireksa.customer.target'
    _inherit = ['mail.thread']
    _description = 'Customer Omzet Target'

    name = fields.Char(string='Name')
    state = fields.Selection([
        ('draft','Draft'),('submit','Waiting for Approval'),
        ('approve','Approved'),('cancel','Cancelled')
    ], string='Status', default='draft', track_visibility='onchange')
    group_id = fields.Many2one('customer.group', string='Customer Group')
    period = fields.Integer(string='Year', track_visibility='onchange')
    date_from = fields.Date(string='From', track_visibility='onchange')
    date_to = fields.Date(string='To', track_visibility='onchange')
    active = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    line_ids = fields.One2many('adireksa.customer.target.line', 'target_id', string='Target Lines')
    company_id = fields.Many2one('res.company', string='Company', track_visibility='onchange')
    notes = fields.Text(string='Notes')
    amount = fields.Float(string='Target Amount')
    submit_by = fields.Many2one('res.users', string='Submit by')
    date_submit = fields.Date(string='Submit Date')
    approve_by = fields.Many2one('res.users', string='Approved by')
    date_approve = fields.Date(string='Approve Date')
    cancel_by = fields.Many2one('res.users', string='Cancel by')
    date_cancel = fields.Date(strin='Cancel Date')

    @api.constrains('period')
    def _check_period(self):
        for record in self:
            # if record.date_from > record.date_to:
            #    raise ValidationError("Please input valid period! Date from cannot be greater than date to.")
            check = self.env['adireksa.customer.target'].search([
                ('group_id','=',record.group_id.id),
                ('period','=',record.period),
                ('company_id','=',record.company_id.id),
                ('id', '!=', record.id)])
            if check:
                raise ValidationError("Please input another period! This period target has already been assigned.")


    def action_submit(self):
        ctl = self.env['adireksa.customer.target.line']
        amount = self.amount
        quarterly = round(amount / 4)
        half_year = round(amount / 2)
        # Quarterly
        qstart = 1
        for x in range(1, 5):
            name = 'Quarter %s' % (str(x))
            subtype = 'q%s' % (str(x))
            qstart = 1 if x == 1 else qend + 1
            qend = 3 if x == 1 else qend + 3
            ctl.create({
                'name': name,
                'frequency': 'quarter',
                'month1': qstart,
                'month2': qend,
                'subtype': subtype,
                'target_id': self.id,
                'amount': quarterly,
                'state': 'submit',
            })
        # Half month
        for x in range(1, 3):
            name = 'First Half Year' if x == 1 else 'Second Half Year'
            subtype = 'firsthalf' if x == 1 else 'secondhalf'
            ctl.create({
                'name': name,
                'frequency': '6month',
                'month1': 1 if x == 1 else 7,
                'month2': 6 if x == 1 else 12, 
                'subtype': subtype,
                'target_id': self.id,
                'amount': half_year,
                'state': 'submit',
            })
        self.write({'state': 'submit', 'submit_by': self.env.user.id, 'date_submit': fields.Date.today()})

    def action_cancel(self):
        self.write({'state': 'cancel', 'cancel_by': self.env.user.id, 'date_cancel': fields.Date.today()})

    def action_draft(self):
        # self.line_ids.unlink()
        self.write({'state': 'draft'})

    def action_approve(self):
        self.line_ids.write({'state': 'approve'})
        self.write({'state': 'approve', 'approve_by': self.env.user.id, 'date_approve': fields.Date.today()})


class CustomerTargetLine(models.Model):
    _name = 'adireksa.customer.target.line'
    _description = 'Customer Omzet Target Line'

    name = fields.Char(string='Name')
    target_id = fields.Many2one('adireksa.customer.target', string='Customer Target', ondelete='cascade')
    state = fields.Selection([
        ('draft','Draft'),('submit','Waiting for Approval'),
        ('approve','Approved'),('cancel','Cancelled')
    ], string='Status', default='draft')
    subtype = fields.Selection([('q1','Quarter 1'),('q2','Quarter 2'),('q3','Quarter 3'),('q4','Quarter 4'),
        ('firsthalf','January - June'),('secondhalf','July - December'),
        ], string='Subtype', default='q1')
    frequency = fields.Selection([('quarter', 'Quarterly'),('6month', '6 Month')], 
        string='Frequency', default='quarter')
    month1 = fields.Integer(string='Start Month')
    month2 = fields.Integer(string='End Month')
    amount = fields.Float(string='Target Amount', default=0.0)
    approve_by = fields.Many2one('res.users', string='Approved by')
    date_approve = fields.Date(string='Approve Date')
    cancel_by = fields.Many2one('res.users', string='Cancel by')
    date_cancel = fields.Date(strin='Cancel Date')

    # @api.constrains('subtype')
    # def _check_subtype(self):
    #     for record in self:
    #         check = self.env['adireksa.customer.target.line'].search([
    #             ('target_id','=',record.target_id.id),
    #             ('subtype','=',record.subtype),
    #             ('id', '!=', record.id)])
    #         if check:
    #             raise ValidationError("Please input another subtype! This subtype has already been assigned.")

    def action_cancel(self):
        self.write({'state': 'draft', 'cancel_by': self.env.user.id, 'date_cancel': fields.Date.today()})

    def action_request_approval(self):
        self.write({'state': 'request_approval'})

    def action_approve(self):
        self.write({'state': 'approve', 'approve_by': self.env.user.id, 'date_approve': fields.Date.today()})
    
    @api.onchange('subtype')
    def onchange_subtype(self):
        if self.subtype in ['q1','q2','q3','q4']:
            if self.subtype == 'q1':
                self.month1 = 1
                self.month2 = 3
            elif self.subtype == 'q2':
                self.month1 = 4
                self.month2 = 6
            elif self.subtype == 'q3':
                self.month1 = 7
                self.month2 = 9
            elif self.subtype == 'q4':
                self.month1 = 10
                self.month2 = 12
            self.frequency = 'quarter'
        else:
            if self.subtype == 'firsthalf':
                self.month1 = 1
                self.month2 = 6
            else:
                self.month1 = 7
                self.month2 = 12
            self.frequency =  '6month'
