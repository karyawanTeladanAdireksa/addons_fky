from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CustomerCashback(models.Model):
    _name = "customer.cashback"
    _description = "Customer Cashback"

    name = fields.Char(string='Customer Cashback Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer')
    nilai_cashback = fields.Float(string='Nilai Cashback')
    state = fields.Selection([('draft', 'Draft'), ('request_approval', 'Request for Approval'), ('approve', 'Approved')], default='draft', string='Status', readonly=True, copy=False, index=True)
    customer_deposit_id = fields.Many2one('account.account', string='Customer Deposit')
    group_ids = fields.Many2many('customer.group', string='Customer Group')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('customer.cashback') or _('New')
        return super(CustomerCashback, self).create(vals)


    def action_request_approval(self):
        self.write({'state': 'request_approval'})
        return True


    def action_approve(self):
        cashback_credit_id = self.env['ir.config_parameter'].sudo().get_param('adireksa_cashback_manual.cashback_credit_id')
        cashback_debit_id = self.env['ir.config_parameter'].sudo().get_param('adireksa_cashback_manual.cashback_debit_id')
        cashback_journal_id = self.env['ir.config_parameter'].sudo().get_param('adireksa_cashback_manual.cashback_journal_id')
        if cashback_journal_id and cashback_credit_id and cashback_debit_id:
                self.env['account.move'].with_context(default_move_type='entry').create({
                    'ref': self.name,
                    'journal_id': cashback_journal_id,
                    'line_ids': [(0, 0, {
                        'name': self.name,
                        'debit': self.nilai_cashback,
                        'account_id': cashback_debit_id,
                    }), (0, 0, {
                        'name': self.name,
                        'credit': self.nilai_cashback,
                        'account_id': cashback_credit_id,
                    })]
                })
                self.write({'state': 'approve'})
        else:
            raise UserError('Configure account setting before creating cashback journal.')
        return True