from odoo import models,fields,api,_

class SalesReturnLine(models.Model):
    _name = "sales.return.line"
    _description = "Sales Return Line"


    return_id = fields.Many2one('sales.return',string="Sales Return")
    product_id = fields.Many2one('product.product',string="Product")
    name = fields.Char(string="Description")
    qty = fields.Float(string="Qty",required=True,default=1)
    brand_product = fields.Many2one('product.brand',string="Brand") 
    condition_id = fields.Many2one('res.condition.product',string="Condition")
    action_type_id = fields.Many2one('res.action.type',string="Return Action",domain="['|',('is_receipt','=',True),('is_delivery','=',True)]")
    notes = fields.Text(string="Notes")
    currency_id = fields.Many2one('res.currency',string="Currency", related="return_id.currency_id")
    price_unit = fields.Float(string="Price Unit",required=True)
    price_subtotal = fields.Monetary(string="Price Subtotal",currency_field="currency_id",compute="_compute_price_subtotal",store=True)
    state = fields.Selection(related="return_id.state")

    receipt_moves_ids = fields.One2many('stock.move','incoming_sales_return_line_id',string="Receipt Moves")
    delivery_moves_ids = fields.One2many('stock.move','outgoing_sales_return_line_id',string="Delivery Moves")

    replacement_action_type_id = fields.Many2one('res.action.type',string="Replacement Action",domain="['|',('is_replacement','=',True),('other_action','=',True)]")
    replacement_product_ids = fields.One2many('replacement.product','return_line_id',string="Replacement Product")
    brand_replacement_ids = fields.One2many('replacement.brand','return_line_id',string="Brand")
    replacement_qty_ids = fields.One2many('replacement.qty', 'return_line_id', string="Qty")   
    replacement_price_subtotal = fields.Float(string="Replacement Subtotal",compute="_compute_replacement_price_subtotal",store=True)
    company_id = fields.Many2one('res.company', string='Company', related='return_id.company_id',store=True, track_visibility='onchange')
    send_back_customer = fields.Boolean(string="Send Back Customer",default=True, compute="_compute_send_back_customer",help="if true user cannot add replacement product")
    use_replacement_action = fields.Boolean(compute="_compute_send_back_customer")
    
    @api.onchange('product_id')
    def onchange_description(self):
        self.name = self.product_id.display_name
        self.price_unit = self.product_id.list_price
        self.brand_product = self.product_id.product_brand
        if not self.action_type_id:
            self.action_type_id = self.env['res.action.type'].search([('is_default_return','=',True)],limit=1).id
        if not self.replacement_action_type_id:
            self.replacement_action_type_id = self.env['res.action.type'].search([('is_default_replacement','=',True)],limit=1).id
          

    @api.depends('price_unit','qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.qty

    @api.depends('replacement_product_ids.price_unit','replacement_product_ids.qty','replacement_product_ids.price_subtotal')
    def _compute_replacement_price_subtotal(self):
        for line in self:
            price_subtotal = 0.0
            for replacement_line in line.replacement_product_ids:
                price_subtotal += replacement_line.price_subtotal
            line.replacement_price_subtotal = price_subtotal

    @api.depends('action_type_id','replacement_action_type_id')
    def _compute_send_back_customer(self):
        for line in self:
            line.send_back_customer = True if line.action_type_id.is_delivery or not line.action_type_id or (line.replacement_action_type_id and not line.replacement_action_type_id.is_replacement) else False
            line.use_replacement_action = True if line.action_type_id.is_delivery or not line.action_type_id else False
            # line.replacement_action_type_id = False
            # line.replacement_product_ids = [(5,0,0)]