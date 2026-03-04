from odoo import models,fields,api,_
from odoo.exceptions import UserError

class SalesAgreement(models.Model):
    _name = "sale.agreement"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Sales Agreement"
    _order = 'create_date DESC'

    name = fields.Char(string="Name",default="New",readonly=True)
    customer_group_id = fields.Many2one('adireksa.customer.target',string="Customer Group")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    create_date = fields.Datetime(string='Create Date', readonly=True, index=True, help="Date on which sales Agreement is created.")
    create_uid = fields.Many2one('res.users', 'Create by', index=True, readonly=True)
    sales_agreement_line_ids = fields.One2many("sale.agreement.line","sales_agreement_id",string="Sales Line")
    state = fields.Selection([('draft','Draft'),
                              ('running','Running'),
                              ('done','Done'),
                              ('unlocked','Unlocked'),
                              ('cancel','Cancelled')],
                              string="State",default="draft",tracking=1)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company.id, track_visibility='onchange')
    
    current_date = fields.Boolean(compute="_compute_current_date")
    sale_order_count = fields.Integer(compute="_compute_saleorder_count")

    def unlink(self):
        for agreement in self:
            if agreement.state not in ('draft', 'cancel'):
                raise UserError(_('Cannot delete Agreement other than Draft and Cancel state'))
        return super(SalesAgreement, self).unlink()

    def action_confirm(self):
        self.state = 'running'

    def action_done(self):
        self.state = 'done'

    def action_unlocked(self):
        self.state = 'unlocked'

    def action_cancel(self):
        self.state = 'cancel'

    def action_to_draft(self):
        self.state = 'draft'

    def action_view_saleorder(self):
        sales_order = self.sales_agreement_line_ids.sale_order_line.order_id
        if not sales_order:
            return {'type':'ir.actions.act_window_close'}
        return {
            'name':_("Sales Order"),
            'type':'ir.actions.act_window',
            'res_model':'sale.order',
            'domain':[('id','in',sales_order.ids)],
            'view_mode':'tree,form',
            'views':[(self.env.ref('sale.view_quotation_tree').id, 'tree'),
                     (self.env.ref('sale.view_order_form').id, 'form')
                    ],
        }
    
    def _compute_saleorder_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sales_agreement_line_ids.sale_order_line.order_id)

    def _compute_current_date(self):
        today = fields.Date.today()
        for rec in self:
            if rec.start_date and rec.end_date and rec.state == 'running':
                if today >= rec.start_date and today <= rec.end_date:
                    rec.current_date = True
                    continue
            rec.current_date = False

    @api.model
    def create(self,vals):
        if vals.get('name','New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.agreement')

        return super(SalesAgreement,self).create(vals)

