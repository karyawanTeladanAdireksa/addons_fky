from odoo import api, fields, models, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class SaleRequest(models.Model):
    _name = "sale.request"
    _description = "Sale Request"

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting For Availability'),
        ('partial', 'Partially Available'),
        ('available', 'Available'), ('quotation', 'Quotation'), ('done', 'Done'), ('cancel', 'Cancel')], string='Status', readonly=True,
        copy=False, index=True, default='draft')

    partner_id = fields.Many2one('res.partner', string='Customer')
    invoice_address = fields.Char(string="Invoice Address")
    delivery_address = fields.Char(string="Delivery Address")
    date_order = fields.Datetime(string="Order Date", copy=False, default=fields.Datetime.now)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    user_id = fields.Many2one('res.users', string='Sales Person', index=True, default=lambda self: self.env.user)

    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address',
                                         help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address',
                                          help="Delivery address for current sales order.")
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')

    request_line = fields.One2many('sale.request.line', 'request_id', string='Sale Request Lines', copy=True)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_discount = fields.Float(string='Discount',
                                   digits=dp.get_precision('Account'),
                                   readonly=True, compute='_amount_all')

    note = fields.Text('Terms and conditions')

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'quotation': [('readonly', False)]}, )
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,
                                  required=True)

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company.id)

    quotation_view_count = fields.Integer(string='Quotation Count', compute='count_quotation')

    check_material_request_btn = fields.Boolean(string='Check Material Request', default=False)

    def action_confirm_order(self):
        self.write({'state': 'waiting'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reverse_order(self):
        if self.request_line:
            for line in self.request_line:
                qty_available = line.product_id.with_context({'warehouse': self.warehouse_id.id}).qty_available
                if line.product_uom_qty <= qty_available:
                    line.write({'is_qty': True})
                else:
                    line.write({'is_qty': False})

            check = False
            for record in self.request_line:
                if record.is_qty:
                    check = True
                else:
                    check = False
                    break
            if check:
                self.write({'state': 'available'})
            else:
                self.write({'state': 'partial'})

    def action_material_request(self):
        vals = {}
        vals['requested_by'] = self.partner_id.id
        vals['source_document'] = self.name
        vals['destination_location'] = self.warehouse_id.lot_stock_id.id
        str_id = self.env['std.material.request'].create(vals)
        sim_obj = self.env['std.item.mr']
        # line_data = []
        for line in self.request_line:
            qty_available = line.product_id.with_context({'warehouse': self.warehouse_id.id}).qty_available
            if line.is_qty == False:
                line_vals = {
                    'product': line.product_id.id,
                    'descript': line.product_id.name,
                    'quantity': line.product_uom_qty - qty_available,
                    'std_mr': str_id.id,
                    'destination_location_id': self.warehouse_id.lot_stock_id.id,
                }
                sim_obj.create(line_vals)
                # line_vals['product'] = line.product_id.id
                # line_vals['descript'] = line.product_id.name
                # line_vals['quantity'] = line.product_uom_qty
                # line_data.append((0, 0, line_vals))
        # vals['product_line'] = line_data

    def action_create_sale_order_partial(self):
        if self.state == "partial":
            warning_txt = 'This Sales Request still has an Outstanding item product. Do you want to do Backorder for outstanding item?'
            return {
                'name': 'Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'sr.message',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_message': warning_txt}
            }

    def action_create_sale_order(self):
        vals = {}
        if self.state == "available":
            vals['partner_id'] = self.partner_id.id
            vals['sale_request_id'] = self.id
            vals['warehouse_id'] = self.warehouse_id.id
            vals['date_order'] = self.date_order
            vals['payment_term_id'] = self.payment_term_id.id
            line_data = []
            for line in self.request_line:
                quotation_ids = self.env['sale.order'].search([('sale_request_id', '=', self.id)])
                if quotation_ids:
                    lines_ids = quotation_ids.mapped('order_line').filtered(lambda a: a.product_id == line.product_id)
                    product_uom_qty = sum(lines_ids.mapped('product_uom_qty'))
                    qty_available = line.product_id.with_context({'warehouse': self.warehouse_id.id}).qty_available
                    remaining_qty = qty_available - product_uom_qty
                    check_all_partial_count = 1
                    if line.product_uom_qty != line.sale_qty and remaining_qty > 0:
                        line_vals = {
                            'product_id': line.product_id.id,
                            'name': line.product_id.name,
                            'product_uom_qty': remaining_qty,
                            'price_unit': line.price_unit,
                            'tax_id': [(6,0,line.tax_id.ids)]
                        }
                        line.write({'sale_qty': line.sale_qty + remaining_qty})
                        line_data.append((0, 0, line_vals))
                else:
                    line_vals = {}
                    if line.product_uom_qty - line.sale_qty > 0:
                        line_vals['product_id'] = line.product_id.id
                        line_vals['name'] = line.product_id.name
                        line_vals['product_uom_qty'] = line.product_uom_qty
                        line_vals['price_unit'] = line.price_unit
                        line_vals['tax_id'] = [(6, 0, line.tax_id.ids)]
                        line.write({'sale_qty': line.product_uom_qty})
                        line_data.append((0, 0, line_vals))
            vals['order_line'] = line_data
            self.env['sale.order'].create(vals)
            self.write({'state': 'done'})

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('sale.request') or _('New')
        vals['name'] = seq
        return super(SaleRequest, self).create(vals)

    @api.depends('request_line.price_total')
    def _amount_all(self):
        """
                Compute the total amounts of the SO.
                """
        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.request_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_discount': order.pricelist_id.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })

    def count_quotation(self):
        for record in self:
            quotation = self.env['sale.order'].search([('sale_request_id', '=', record.id)])
            record.quotation_view_count = len(quotation)

    def action_quotation_view(self):
        quotation = self.env['sale.order'].search([('sale_request_id', '=', self.id)])
        action = self.env.ref('sale.action_orders').read()[0]
        if len(quotation) > 1:
            action['domain'] = [('id', 'in', quotation.ids)]
        elif len(quotation) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotation.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class SaleRequestLine(models.Model):
    _name = "sale.request.line"
    _description = "Sale Request Line"

    request_id = fields.Many2one('sale.request', string='Sale Request Reference', index=True, copy=False)

    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(string='Description')
    product_uom_qty = fields.Float(string="Order Qty", digits=dp.get_precision('Product Unit of Measure'), default=1.0)

    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    warehouse_id = fields.Many2one('stock.warehouse', string="Source Warehouse")
    cost = fields.Float(string="Cost")
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    date_requested = fields.Datetime(string="Requested Date", copy=False, default=fields.Datetime.now)

    tax_id = fields.Many2many('account.tax', string='Taxes',
                              domain=['|', ('active', '=', False), ('active', '=', True)])
    delivery_lead_time = fields.Float(string="Delivery Lead Time")
    last_sale_price = fields.Integer(string="Last Sales Price")
    last_sale_price_customer = fields.Integer(string="Last Sales Price  Customer")

    qty_invoiced = fields.Float(string='Invoiced', store=True, readonly=True,
                                digits=dp.get_precision('Product Unit of Measure'))
    qty_delivered = fields.Float(string='Delivered', copy=False, digits=dp.get_precision('Product Unit of Measure'),
                                 default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    currency_id = fields.Many2one(related='request_id.currency_id', store=True, string='Currency', readonly=True)
    salesman_id = fields.Many2one(related='request_id.user_id', store=True, string='Salesperson', readonly=True)
    company_id = fields.Many2one(related='request_id.company_id', string='Company', store=True, readonly=True)

    is_qty = fields.Boolean(string='Is Qty Avaliable', default=False)
    sale_qty =  fields.Float(string="Sale Qty", copy=False)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.request_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.request_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
