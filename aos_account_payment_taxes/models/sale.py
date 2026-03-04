
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    
    @api.depends('price_unit', 'discount', 'tax_id', 'product_uom_qty', 'tax_wth_id',
                 'order_id.partner_id', 'order_id.currency_id', 'order_id.company_id',
                 'order_id.date_order')
    def _compute_price_wth(self):
        taxes = self.invoice_line_wth_tax_ids.compute_all(self.price_subtotal, self.currency_id, self.quantity, self.product_id, self.partner_id)['taxes']
        amount_wth_line = 0.0
        for tax in taxes:
            amount_wth_line += tax['amount']
        self.amount_wth_line = amount_wth_line
        
    amount_wth_line = fields.Monetary(string='Wth Tax Amount',
        store=True, readonly=True, compute='_compute_price_wth')    
    tax_wth_id = fields.Many2many('account.tax', string='Wth Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res['invoice_line_wth_tax_ids'] = [(6, 0, self.tax_wth_id.ids)]
        return res
    
#     
#     def _prepare_invoice_line(self, qty):
#         """
#         Prepare the dict of values to create the new invoice line for a sales order line.
# 
#         :param qty: float quantity to invoice
#         """
#         self.ensure_one()
#         res = {}
#         product = self.product_id.with_context(force_company=self.company_id.id)
#         account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
# 
#         if not account and self.product_id:
#             raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
#                 (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))
# 
#         fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
#         if fpos and account:
#             account = fpos.map_account(account)
# 
#         res = {
#             'name': self.name,
#             'sequence': self.sequence,
#             'origin': self.order_id.name,
#             'account_id': account.id,
#             'price_unit': self.price_unit,
#             'quantity': qty,
#             'discount': self.discount,
#             'uom_id': self.product_uom.id,
#             'product_id': self.product_id.id or False,
#             'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
#             'account_analytic_id': self.order_id.analytic_account_id.id,
#             'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
#             'display_type': self.display_type,
#         }
#         return res