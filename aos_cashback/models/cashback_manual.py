from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CashbackManual(models.Model):
    _name = 'cashback.manual'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cashback Manual'


    @api.model
    def default_get_year(self):
        return fields.date.today().year
        
    name = fields.Char(string="Name")
    group_id = fields.Many2one('adireksa.customer.target', string='Customer Group',required=True)
    company_id = fields.Many2one('res.company', 'Company', related="group_id.company_id" ,readonly=True)
    user_id = fields.Many2one('res.users', 'Create By', default=lambda self: self.env.user.id,readonly=True)
    value = fields.Float(string="Value")
    default_posting = fields.Selection([('debit', 'Debit'),('credit', 'Credit')], required=True)
    ref = fields.Char('Reference',required=True)
    state = fields.Selection([('draft', 'Draft'),('waiting', 'Waiting For Approval') ,('confirm', 'Approved'), ('cancel', 'Cancel')],
                             default='draft', string='Status', readonly=True, copy=False, index=True)
    memo = fields.Char(string="Memo")
    year = fields.Float(default=default_get_year)

    def unlink(self):
        for cashback in self:
            if cashback.state not in ('draft', 'cancel'):
                raise UserError(_('Cannot delete Manual Cashbach other than draft or cancel state'))
        return super(CashbackManual, self).unlink()
    
    # @api.onchange('value')
    # def onchange_default_posting(self):
    #     self.default_posting = 'debit'
    #     if self.value < 0:
    #         self.default_posting = 'credit'

    def action_waiting(self):
        self.state = 'waiting'
    
    def write(self, vals):
        if vals.get('value'):
            if vals.get('value') <= 0 :
                raise UserError(_('Value Cashback Tidak Bisa Minus'))
        return super(CashbackManual, self).write(vals)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cashback.manual') or _('New')
        return super(CashbackManual, self).create(vals)
    
    def action_confirm(self):
        self.state = 'confirm'
        mcc_id = self.env['master.customer.cashback'].search([('group_id','=',self.group_id.id),('company_id','=',self.company_id.id)])
        self.env['manual.cashback.lines'].create({
            'name':self.name,
            'date':self.create_date.date(),
            'value':self.value,
            'state':'approve',
            'user_id':self.user_id.id,
            'default_posting':self.default_posting,
            'cashback_id': mcc_id.id,
            'reference':self.ref
        })
        self.env['cashback.lines'].create({
                                'name':self.name,
                                'group_id':self.group_id.id,
                                'reference': self.ref,
                                'cashback_id': mcc_id.id,
                                'cashback_rule':'Manual Cashback',
                                'date': self.create_date.date(),
                                'value': self.value,
                                'default_posting':self.default_posting,
                                'state': 'approve',
                                # 'cashback_rule_id': [(6, 0, line_id)],
                            })

