from odoo import models,fields,api
from odoo.exceptions import UserError

class SalesAgreementLine(models.Model):
    _name = "sale.agreement.line"
    _description = "Sales Agreement Line"
    _rec_name = "name"

    name = fields.Char(string="Name",compute="_compute_display_name",store=True)
    sales_agreement_id = fields.Many2one('sale.agreement',string="Agreement")
    customer_group_id = fields.Many2one('adireksa.customer.target',string="Customer Group",related='sales_agreement_id.customer_group_id',store=True)
    category_id = fields.Many2one('internal.category',string="Internal Category",required=True)
    quantity_commitment = fields.Float(string="Quantity Commitment")
    quantity_order = fields.Float(string="Quantity Order",readonly=True,store=True,compute="_compute_quantity_order")
    achievement_progress = fields.Float(string="Achievement (%)",compute="_compute_quantity_order")
    sale_order_line = fields.One2many('sale.order.line','sale_agreement_line_id',string="Order Line")
    state = fields.Selection([('draft','Draft'),('running','Running'),('done','Locked'),('unlocked','Unlocked'),('cancel','Cancelled')],string="State",default="draft",related="sales_agreement_id.state")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company.id, track_visibility='onchange')
    
    
    @api.depends('category_id','sales_agreement_id','quantity_commitment')
    def _compute_display_name(self):
        for line in self:
            line.display_name = line.name = line.sales_agreement_id.name, line.sales_agreement_id.customer_group_id.name
            # line.display_name = line.name = line.sales_agreement_id.name+ " / " +line.sales_agreement_id.customer_group_id.name

    @api.depends('sale_order_line.product_uom_qty')
    def _compute_quantity_order(self):
        for line in self:
            sales_order_line = line.sale_order_line.filtered(lambda line:line.state != 'cancel')
            if not sales_order_line:
                quantity_order = 0.0
                achievement_progress = 0.0
            else:
                quantity_order = sum(sales_order_line.mapped('product_uom_qty'))
                achievement_progress = (sum(sales_order_line.mapped('product_uom_qty')) * 100) / (line.quantity_commitment or 1.0)
            line.quantity_order = quantity_order
            line.achievement_progress = achievement_progress