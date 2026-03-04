from odoo import models,fields

class ResCompany(models.Model):
    _inherit = "res.company"

    cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), ('customer_invoice', 'Customer Invoice')], string="Cashback Deduction Option")
    cashback_role = fields.Selection([('as_discount', 'As Discount'), ('as_expense', 'As Expense (JE on progress)')], default='as_discount',
                                                  string="Cashback Role")