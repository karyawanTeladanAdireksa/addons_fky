# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime


class CreditLimitRequest(models.Model):
    _name='credit.limit.request'
    _description = "Credit Limit Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Name")
    request_id = fields.Many2one('res.users', "Requested By", default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner',"Customer")
    create_date = fields.Date("Creation Date")
    credit_amount = fields.Float("Credit Amount Request")
    last_credit_limit = fields.Float("Last Credit Limit", related="partner_id.credit_limit" ,help="Pull from credit limit of customer", readonly=True)
    description = fields.Text("Description")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ], string='Status', readonly=True, copy=False, index=True,track_visibility='onchange', tracking=3, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company.id, track_visibility='onchange')


    
    def request_approve(self):
        self.state = 'waiting_approval'
        return True

    
    def credit_amount_approve(self):
        self.state = 'approved'
        self.partner_id.credit_limit = self.credit_amount or 0.0
        self.partner_id.check_credit = True
        return True

    
    def credit_request_reject(self):
        self.state = 'rejected'
        return True