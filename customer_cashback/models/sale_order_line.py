# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        max_cashback = self.env['ir.config_parameter'].sudo().get_param('customer_cashback.max_cashback')
        res.update({
                'max_cashback': max_cashback
            })
        return res


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({'cashback_value': self.cashback_value})
        return res

    cashback_per = fields.Float('Cashback %')
    max_cashback = fields.Float(string='Max Cashback')
    cashback_value = fields.Float('Cashback Value', compute='compute_cashback_value')
    cashback_deduction_option = fields.Selection([('sale_order', 'Sale Order'), ('customer_invoice', 'Customer Invoice')], related="company_id.cashback_deduction_option", string="Cashback Deduction Option", store=True)

    @api.depends('cashback_per', 'amount_untaxed', 'discount_amount', 'amount_tax')
    def compute_cashback_value(self):
        for rec in self:
            rec.cashback_value = ((rec.amount_untaxed - rec.discount_amount + rec.amount_tax)* rec.cashback_per)/100.0

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # for rec in self:
            # if rec.partner_id.get_cashback or rec.partner_id.cashback_generate == 'auto':
                # domain = []
                # if rec.partner_id.category_id:
                    # domain += [('group_id', 'in', rec.partner_id.category_id.ids)]
                # else:
                    # domain += [('partner_id', '=', rec.partner_id.id)]
                # mcc_rec = self.env['master.customer.cashback'].search(domain, limit=1)
                #
                # type_in = self.env['cashback.type'].search([('id', '=', self.env.ref('customer_cashback.cashback_type_so_in').id)])
                # type_out = self.env['cashback.type'].search([('id', '=', self.env.ref('customer_cashback.cashback_type_so_out').id)])
                # if mcc_rec:
                    # total = 0.0
                    # if rec.cashback_value > 0:
                        # self.env['cashback.lines'].create({'name': rec.name,
                                      # 'partner_id' : rec.partner_id.id,
                                      # 'date': rec.date_order, 
                                      # 'type_id': type_out.id,
                                      # 'value': rec.cashback_value,
                                      # 'reference': rec.client_order_ref,
                                      # 'state': 'pending',
                                      # 'cashback_id': mcc_rec.id})
                    # for line in rec.order_line:
                        # if line.cashback_value > 0:
                            # self.env['cashback.lines'].create({'name': rec.name,
                                          # 'partner_id' : rec.partner_id.id,
                                          # 'date': rec.date_order, 
                                          # 'type_id': type_in.id,
                                          # 'value': line.cashback_value,
                                          # 'reference': rec.client_order_ref,
                                          # 'state': 'pending',
                                          # 'cashback_id': mcc_rec.id})
                            # total += line.cashback_value
                            # mcc_rec.cashback_in += line.cashback_value
                    # if rec.cashback_deduction_option == 'customer_invoice' and  rec.partner_id.cashback_generate == 'auto':
                        # cashback_value = ((rec.amount_untaxed - rec.discount_amount + rec.amount_tax)* rec.max_cashback)/100.0
                        # self.env['cashback.lines'].create({'name': rec.name,
                                          # 'partner_id' : rec.partner_id.id,
                                          # 'date': rec.date_order, 
                                          # 'type_id': type_in.id,
                                          # 'value': cashback_value,
                                          # 'reference': rec.client_order_ref,
                                          # 'state': 'pending',
                                          # 'cashback_id': mcc_rec.id})
                        # total += cashback_value
                        # mcc_rec.cashback_in += line.cashback_value
                        # if mcc_rec.journal_id and mcc_rec.account_id and mcc_rec.expense_account_id and total > 0.0:
                            # self.env['account.move'].create({
                                # 'ref': rec.name,
                                # 'journal_id': mcc_rec.journal_id.id,
                                # 'line_ids': [(0, 0, {
                                    # 'name': rec.name,
                                    # 'partner_id': rec.partner_id.id,
                                    # 'debit': total,
                                    # 'account_id': mcc_rec.expense_account_id.id,
                                # }), (0, 0, {
                                    # 'name': self.name,
                                    # 'partner_id': rec.partner_id.id,
                                    # 'credit': total,
                                    # 'account_id': mcc_rec.account_id.id,
                                # })]
                            # })
        return res


    @api.depends('order_line.price_total', 'cashback_value')
    def _amount_all(self):
        res = super(SaleOrder, self)._amount_all()
        for rec in self:
            rec.amount_total -= rec.cashback_value
        return res

class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    cashback_value = fields.Float(compute='compute_cashback_value', string='Cashback Value', readonly=False)
    get_cashback = fields.Boolean(related='order_id.partner_id.get_cashback', store=True)
    edit_cashback = fields.Boolean(related='order_id.partner_id.edit_cashback', store=True)

    @api.depends('product_id', 'price_subtotal', 'price_total')
    def compute_cashback_value(self):
        for rec in self:
            if rec.order_id.partner_id.get_cashback:
                domain = [('product_id', '=', rec.product_id.id)]
                if rec.order_id.partner_id.category_id:
                    domain += [('cashback_id.group_id', 'in', rec.order_id.partner_id.category_id.ids)]
                else:
                    domain += [('cashback_id.partner_id', '=', rec.order_id.partner_id.id)]
                mcp_line = self.env['cashback.product.lines'].search(domain, limit=1)
                if mcp_line:
                    rec.cashback_value = (rec.price_subtotal * mcp_line.value) / 100
            