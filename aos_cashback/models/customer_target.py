# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import math
import calendar


class CustomerTarget(models.Model):
    _name = 'adireksa.customer.target'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer Omzet Target'

    name = fields.Char(string='Customer Group',required=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('waiting', 'Waiting for Approval'),
        ('approve', 'Running'), ('cancel', 'Cancelled')
    ], string='Status', default='draft', track_visibility='onchange')
    #group_id = fields.Many2one('customer.group', string='Customer Group')
    period = fields.Integer(string='Year', track_visibility='onchange')
    date_from = fields.Date(string='From', track_visibility='onchange')
    date_to = fields.Date(string='To', track_visibility='onchange')
    active = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    line_ids = fields.One2many('adireksa.customer.target.line', 'target_id', string='Target Lines')
    # company_id = fields.Many2one('res.company', string='Company', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    notes = fields.Text(string='Notes')
    amount = fields.Float(string='Target Amount')
    area_id = fields.Many2one(comodel_name="customer.area", string="Group Area", required=False, )
    wilayah_target = fields.Float(string='Target Wilayah',related="area_id.wilayah_target",readonly=True)
    partner_line_ids = fields.One2many('partner.line.target','target_id')
    group_class_id = fields.Many2one('cashback.class.group',string="Group Class")

    _sql_constraints = [
        ('unique_period', 'Check (1=1)', 'This Year Target Already Exists')
    ]
    # partner_ids = fields.One2many(comodel_name="res.partner", inverse_name="group_id", string="", required=False, )


    # submit_by = fields.Many2one('res.users', string='Submit by')
    # date_submit = fields.Date(string='Submit Date')
    # approve_by = fields.Many2one('res.users', string='Approved by')
    # date_approve = fields.Date(string='Approve Date')
    # cancel_by = fields.Many2one('res.users', string='Cancel by')
    # date_cancel = fields.Date(strin='Cancel Date')

    # @api.constrains('period')
    # def _check_period(self):
    #     for record in self:
    #         # if record.date_from > record.date_to:
    #         #    raise ValidationError("Please input valid period! Date from cannot be greater than date to.")
    #         check = self.env['adireksa.customer.target'].search([
    #             ('group_id', '=', record.group_id.id),
    #             ('period', '=', record.period),
    #             ('company_id', '=', record.company_id.id),
    #             ('id', '!=', record.id)])
    #         if check:
    #             raise ValidationError("Please input another period! This period target has already been assigned.")

    @api.model
    def create(self,vals):
        customer_target = self.env['adireksa.customer.target'].search(['&',('name','=',vals.get('name')),('period','=',vals.get('period'))])
        if self :
            customer_target = False
            vals['period'] = False
            vals['amount'] = False
        if customer_target:
            raise UserError(_('Customer Group Sudah Memiliki Target Pada Period Ini'))
        res = super(CustomerTarget,self).create(vals)
        master = self.env['master.customer.cashback'].search([('cashback_name','=',res.name)])
        if not master:
            master = self.env['master.customer.cashback'].search([('cashback_name','=',res.name + ' Cashback')])
        if not master:
            self.env['master.customer.cashback'].create({
                'name':self.env['ir.sequence'].next_by_code('master.customer.cashback') or _('New'),
                'group_id':res.id,
                'cashback_name':res.name + ' Cashback',
                'company_id':res.company_id.id,
            })
        else :
            master.write({'group_id':res.id})
        return res

    def fetch_customer_target(self):
        target_obj = self.env['adireksa.customer.target'].search([('period','=',fields.date.today().year - 1)])
        partner_id = self.env['res.partner'].search([])
        for target in target_obj:
            current_target = target.search([('name','=',target.name),('period','=',target.period + 1)])
            if current_target:
                current_target.write({'partner_line_ids':target.partner_line_ids.ids})
        for rec in partner_id:
            if rec.group_id.period != fields.date.today().year:
                target = self.env['adireksa.customer.target'].search([('name','=',rec.group_id.name),('period','=',fields.date.today().year)],limit=1)
                if target:
                    rec.write({'group_id':target.id})
        

    def action_submit(self):
        ctl = self.env['adireksa.customer.target.line']
        amount = self.amount
        quarterly = round(amount / 4)
        half_year = round(amount / 2)
        monthly = round(amount / 12)
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
        ctl.create({
            'name': 'Monthly',
            'frequency': 'month',
            'month1': 1 ,
            'month2': 12,
            'subtype': 'month',
            'target_id': self.id,
            'amount': monthly,
            'state': 'submit',
        })
        ctl.create({
            'name': 'Wilayah',
            'frequency': 'month',
            'month1': 0,
            'month2': 0,
            'subtype': 'wilayah',
            'target_id': self.id,
            'amount': self.wilayah_target,
            'state': 'submit',
        })
        self.sudo().checking_approval_matrix(require_approver=True)
        self.write({'state': 'waiting'})

    def action_cancel(self):
        self.write({'state': 'cancel',})
        self.line_ids.write({'state': 'cancel'})
    
    def button_confirm(self):
        if self.year == 0 or self.amount == 0:
            raise UserError(_('Customer Group Belum Memiliki Target Atau Period'))
        res =  super(CustomerTarget,self).button_confirm()
        return res 
    def action_draft(self):
        # self.line_ids.unlink()
        self.write({'state': 'draft'})
        self.line_ids = False


    def action_approve(self):
        # self.action_submit()
        self.line_ids.write({'state': 'approve'})
        self.write({'state': 'approve',})


class CustomerTargetLine(models.Model):
    _name = 'adireksa.customer.target.line'
    _description = 'Customer Omzet Target Line'

    name = fields.Char(string='Name')
    target_id = fields.Many2one('adireksa.customer.target', string='Customer Target', ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft'), ('submit', 'Waiting for Approval'),
        ('approve', 'Approved'), ('cancel', 'Cancelled')
    ], string='Status', default='draft')
    subtype = fields.Selection([('q1', 'Quarter 1'), ('q2', 'Quarter 2'), ('q3', 'Quarter 3'), ('q4', 'Quarter 4'),
                                ('firsthalf', 'January - June'), ('secondhalf', 'July - December'),('month', 'Month'),('wilayah', 'Wilayah')
                                ], string='Subtype', default='q1')
    frequency = fields.Selection([('wilayah', 'Wilayah'),('month', 'Monthly'),('quarter', 'Quarterly'), ('6month', '6 Month')],
                                 string='Frequency', default='quarter')
    month1 = fields.Integer(string='Start Month')
    month2 = fields.Integer(string='End Month')
    amount = fields.Float(string='Target Amount', default=0.0)
    # approve_by = fields.Many2one('res.users', string='Approved by')
    # date_approve = fields.Date(string='Approve Date')
    # cancel_by = fields.Many2one('res.users', string='Cancel by')
    # date_cancel = fields.Date(strin='Cancel Date')

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
        self.write({'state': 'draft'})

    def action_request_approval(self):
        self.write({'state': 'request_approval'})

    def action_approve(self):
        self.write({'state': 'approve'})

    @api.onchange('subtype')
    def onchange_subtype(self):
        if self.subtype in ['q1', 'q2', 'q3', 'q4']:
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
        elif self.subtype == 'month':
            self.month1 = 1
            self.month2 = 12
            self.frequency = 'month'
        elif self.subtype == 'wilayah':
            self.month1 = 0
            self.month2 = 0
            self.frequency = 'month'
        else:
            if self.subtype == 'firsthalf':
                self.month1 = 1
                self.month2 = 6
            else:
                self.month1 = 7
                self.month2 = 12
            self.frequency = '6month'

class CustomerArea(models.Model):
    _name = 'customer.area'
    _rec_name = 'name'
    _description = 'Customer Area'

    name = fields.Char(string="", required=False, )
    wilayah_target = fields.Float(string='Target Wilayah')
    formula_percent = fields.Float(string="Percent Per Wilayah")
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.user.company_id.id)

class PartnerLineTarget(models.Model):
    _name = 'partner.line.target'
    _description = 'Partner Line Target'

    name = fields.Char(string="", required=False,)
    target_id = fields.Many2one('adireksa.customer.target')
    partner_id = fields.Many2one('res.partner',string="Name")
    area_id = fields.Many2one('customer.area', related="partner_id.area_id")
    phone = fields.Char( related="partner_id.phone")
    email = fields.Char( related="partner_id.email")
    user_id = fields.Many2one('res.users' ,related="partner_id.user_id")
    activity_ids = fields.One2many('mail.activity' ,related="partner_id.activity_ids")
    city = fields.Char( related="partner_id.city")
    country_id = fields.Many2one('res.country', related="partner_id.country_id")
    ref = fields.Char( related="partner_id.ref")
    state = fields.Selection([
        ('draft', 'Draft'), ('waiting', 'Waiting for Approval'),
        ('approve', 'Approved'), ('reject', 'Not Approved')
    ], string='Status', default='draft', track_visibility='onchange',related="partner_id.state")
    company_id = fields.Many2one('res.company',related="partner_id.company_id")

    @api.model
    def create(self,vals):
        res = super(PartnerLineTarget,self).create(vals)
        res.partner_id.group_id = res.target_id.id
        return res