from odoo import models,fields,api,Command,_
from odoo.tools import float_compare
from odoo.exceptions import UserError
class SalesAgreementToSalesOrder(models.TransientModel):
    _name = "sales.agreement.to.sales.order"
    _description = "Sales Agreement To Sales Order"

    customer_group_id = fields.Many2one('adireksa.customer.target',string="Customer Group")
    partner_id = fields.Many2one('res.partner',string="Customer",required=True)
    agreement_id = fields.Many2one('sale.agreement',string="Sale Agreement")
    agreement_line_ids = fields.Many2many('sale.agreement.line',string="Sale Agreement Line")

    line_ids = fields.One2many('sales.agreement.line.to.sales.order.line','wiz_id')

    def _prepare_values_sale_order_line(self,agreement_line,sale_line_agreement,sale_agreement_id):
        agreement_line.ensure_one()
        taxes = agreement_line.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.agreement_id.company_id.id)
        taxes_ids = [Command.set(taxes.ids)]
        return {
            'product_id':agreement_line.product_id.id,
            'name':agreement_line.product_id.display_name,
            'price_unit':agreement_line.product_id.list_price,
            'product_uom_qty':agreement_line.qty_to_order,
            'sale_agreement_line_id':sale_line_agreement.id,
            'sale_agreement_id':sale_agreement_id.id,
            'internal_category':agreement_line.category_id.id,
            'tax_id':taxes_ids
        }

    def action_confirm(self):
        internal_category = self.agreement_line_ids.mapped('category_id')
        values_line = []
        for categ in internal_category:
            agreement_line = self.line_ids.filtered(lambda x:x.category_id.id == categ.id)
            sale_agreement_line = self.agreement_line_ids.filtered(lambda x:x.category_id.id == categ.id)
            for line in agreement_line:
                values_line += [Command.create(self._prepare_values_sale_order_line(line,sale_agreement_line,self.agreement_id))]
        # Order without internal category
        agreement_line = self.line_ids.filtered(lambda x:x.category_id.id not in internal_category.ids)
        for line in agreement_line:
            values_line += [Command.create(self._prepare_values_sale_order_line(line,self.env['sale.agreement.line'],self.agreement_id))]

        order_values = {
            'partner_id':self.partner_id.id,
            'date_order':fields.Date.today(),
            'order_line':values_line
        }
        self.env['sale.order'].create(order_values)
        
    @api.model
    def default_get(self,fields_list):
        res = super(SalesAgreementToSalesOrder,self).default_get(fields_list)
        if 'agreement_line_ids' in fields_list and not res.get('agreement_line_ids'):
            res['agreement_line_ids'] = [Command.set(self.env['sale.agreement'].browse(res.get('agreement_id',[])).sales_agreement_line_ids.ids)]
        return res
    
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(SalesAgreementToSalesOrder,self).fields_get(allfields,attributes)
        agreement_data = self.env['sale.agreement'].browse(self.env.context.get('active_id'))
        if 'partner_id' in res:
            res['partner_id']['domain'] = [('id','in',agreement_data.customer_group_id.partner_line_ids.partner_id.ids)]
        return res

class SalesAgreementLineToSalesOrderLine(models.TransientModel):
    _name = "sales.agreement.line.to.sales.order.line"
    _description = "Sales Agreement To Sales Order"

    wiz_id = fields.Many2one('sales.agreement.to.sales.order')
    product_id = fields.Many2one('product.product',string="Product",required=True)
    category_id = fields.Many2one('internal.category',string="Internal Category",readonly=True)
    qty_to_order = fields.Float(string="Quantity",required=True)
    agreement_id = fields.Many2one('sale.agreement',string="Sale Agreement",related="wiz_id.agreement_id")

    # @api.onchange('wiz_id')
    # def onchange_domain_category(self):
    #     domain = []
    #     if not self.wiz_id.agreement_line_ids:
    #         domain += [('id','in',self.wiz_id.agreement_id.sales_agreement_line_ids.category_id.ids)]
    #     else:
    #         domain += [('id','in',self.wiz_id.agreement_line_ids.category_id.ids)]

    #     return {'domain':{'category_id': domain}}

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.category_id = self.product_id.internal_category.id