# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_cashback = fields.Float("Max Cashback(%)",config_parameter='customer_cashback.max_cashback')
    cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), ('customer_invoice', 'Customer Invoice')],
                                                 related="company_id.cashback_deduction_option", string="Cashback Deduction Option",config_parameter='customer_cashback.cashback_deduction_option')
    cashback_role = fields.Selection([('as_discount', 'As Discount'), ('as_expense', 'As Expense (JE on progress)')], default='as_discount',
                                                 related="company_id.cashback_role", string="Cashback Role",config_parameter='customer_cashback.cashback_role')
    active_today_cashback_so = fields.Boolean('Today',config_parameter='customer_cashback.active_today_cashback_so')
    active_month_cashback_so = fields.Integer('Month',config_parameter='customer_cashback.active_month_cashback_so')
    active_day_cashback_so = fields.Integer('Day',config_parameter='customer_cashback.active_day_cashback_so')