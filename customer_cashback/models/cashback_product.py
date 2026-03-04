# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MasterCashbackProduct(models.Model):

    _name = "master.cashback.product"
    _description = "Master Cashback Product"

    name = fields.Char(string='Number', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    cashback_type = fields.Selection([('group', 'Customer Group'), ('customer', 'Customer')], default='customer', string='Cashback Type')
    partner_id = fields.Many2one('res.partner', string='Customer')
    group_id = fields.Many2one('customer.group', string='Customer Group')
    product_categ_ids = fields.Many2many('product.category', string='Product Categories')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')], default='draft', string='Status', readonly=True, copy=False, index=True)
    line_ids = fields.One2many('cashback.product.lines', 'cashback_id')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('master.cashback.product') or _('New')
        return super(MasterCashbackProduct, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'confirm'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True


class CashbackProductLines(models.Model):

    _name = 'cashback.product.lines'
    _description = 'Cashback Lines'

    @api.depends('product_id')
    def _compute_product_attribute(self):
        for rec in self:
            rec.attribute_value_ids = rec.product_id.attribute_line_ids.ids

    product_id = fields.Many2one('product.product', 'Product')
    hs_code = fields.Char(string='Part Number')
    attribute_value_ids = fields.Many2many('product.template.attribute.line',compute="_compute_product_attribute",  string="Motor Type")
    value = fields.Float('Value(%)')
    cashback_id = fields.Many2one('master.cashback.product')
