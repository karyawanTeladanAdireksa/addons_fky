from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CashbackInternalCategory(models.Model):
    _name = 'cashback.internal.category'
    _inherit = ['mail.thread']
    _description = 'Cashback Internal Category'

    name = fields.Char(string="Name")
    group_id = fields.Many2one('adireksa.customer.target')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    internal_category_id = fields.Many2one('internal.category')
    invoice_line_ids = fields.Many2many('account.move.line')
    state = fields.Selection([('draft', 'Draft'),('waiting', 'Waiting For Approval') ,('approve', 'Approved'), ('cancel', 'Cancel')],
                            default='draft', string='Status', readonly=True, copy=False, index=True)
    group_class_id = fields.Many2one('cashback.class.group',string="Group Class",related='group_id.group_class_id')

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
    def generate_cashback_internal(self):
        move = self.env['account.move'].search([('invoice_date','>=',self.start_date),('move_type','=','out_invoice'),('invoice_date','<=',self.end_date)],limit=10)
        move_line = move.invoice_line_ids.filtered(lambda x:x.internal_category.id == self.internal_category_id.id and x.internal_bool == False)
        if move_line :
            for rec in move_line:
                rec.subtotal_internal = rec.quantity * rec.price_unit
                rec.internal_bool = True
            self.invoice_line_ids = move_line.ids
            mcc_id = self.env['master.customer.cashback'].search([('group_id','=',self.group_id.id),('company_id','=',self.company_id.id)])
            value = sum(move_line.mapped('subtotal_internal')) * int(self.persent_cashback) / 100
            self.env['cashback.internal.category.lines'].create({
                'name':self.name,
                'date':self.create_date.date(),
                'value':value,
                'state':'approve',
                'user_id':self.env.user.id,
                'cashback_id': mcc_id.id,
                'reference':"Internal Category Cashback "+ self.name
            })
            self.env['cashback.lines'].create({
                                    'name':self.name,
                                    'group_id':self.group_id.id,
                                    'reference': "Internal Category Cashback "+ self.name,
                                    'cashback_id': mcc_id.id,
                                    'cashback_rule':'Internal Category Cashback',
                                    'date': self.create_date.date(),
                                    'value': value,
                                    'default_posting':'debit',
                                    'state': 'approve',
                                    # 'cashback_rule_id': [(6, 0, line_id)],
                                })
    def action_confirm(self):
        self.state = 'approve'


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cashback.internal.category') or _('New')
        return super(CashbackInternalCategory, self).create(vals)