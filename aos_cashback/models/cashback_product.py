from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CashbackProduct(models.Model):
    _name = 'cashback.product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cashback Product'

    name = fields.Char(string="Name")
    group_id = fields.Many2one('adireksa.customer.target')
    group_class_id = fields.Many2one('cashback.class.group',string="Group Class")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    product_id = fields.Many2one('product.product')
    invoice_line_ids = fields.Many2many('account.move.line')
    state = fields.Selection([('draft', 'Draft'),('waiting', 'Waiting For Approval') ,('approve', 'Approved'), ('cancel', 'Cancel')],
                            default='draft', string='Status', readonly=True, copy=False, index=True)

    persent_cashback = fields.Selection([
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
        ('6','6'),
        ('7','7'),
        ('8','8'),
        ('9','9'),
        ('10','10')],default="1", string="Percent Cashback")


    def unlink(self):
        for prod in self:
            if prod.state not in ('draft', 'cancel'):
                raise UserError(
                    _(
                        'You can not delete the Cashback Product Class document, The Document can only be deleted in draft or cancel status'))
        return super(CashbackProduct, self).unlink()
    
    def generate_cashback_internal(self):
        move = self.env['account.move'].search([('invoice_date','>=',self.start_date),('invoice_date','<=',self.end_date),('state','=','posted'),('move_type','=','out_invoice'),('group_id','!=',False)])
        # ['in_invoice','in_refund']
        move_line = move.invoice_line_ids.filtered(lambda x:x.product_id.id == self.product_id.id and x.product_bool == False)
        group_id = move_line.mapped('move_id').group_id
        if group_id :
            for group in group_id:
                move_line_id = move_line.filtered(lambda x:x.group_id.id == group.id)
                for rec in move_line_id:
                    rec.subtotal_internal = rec.quantity * rec.price_unit
                    rec.product_bool = True
                mcc_id = self.env['master.customer.cashback'].search([('group_id','=',group.id),('group_class_id','=',group.group_class_id.id),('company_id','=',self.company_id.id)])
                value = sum(move_line_id.mapped('subtotal_internal')) * int(self.persent_cashback) / 100
                self.env['cashback.product.lines'].create({
                    'name':self.name,
                    'date':self.create_date.date(),
                    'value':value,
                    'state':'approve',
                    'user_id':self.env.user.id,
                    'cashback_id': mcc_id.id,
                    'reference':"Cashback Product "+ self.name
                })
                self.env['cashback.lines'].create({
                                        'name':self.name,
                                        'group_id':self.group_id.id,
                                        'reference': "Cashback Product "+ self.name,
                                        'cashback_id': mcc_id.id,
                                        'cashback_rule':'Cashback Product',
                                        'date': self.create_date.date(),
                                        'value': value,
                                        'default_posting':'debit',
                                        'state': 'approve',
                                        # 'cashback_rule_id': [(6, 0, line_id)],
                                    })
            self.invoice_line_ids = move_line.ids
    def action_confirm(self):
        self.state = 'approve'


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cashback.product') or _('New')
        return super(CashbackProduct, self).create(vals)