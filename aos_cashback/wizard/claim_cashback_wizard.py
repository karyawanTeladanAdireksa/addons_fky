from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class WizardClaimCashback(models.TransientModel):
    _name = 'claim.cashback.wizard'
    _description = 'Claim Cashback Wizard'


    amount_total = fields.Float(string="Total Invoice",readonly=True)
    max_cashback = fields.Float(string="Maximum Cashback",readonly=True,compute="_compute_maxcashback")
    saldo_cashback =fields.Float(string="Saldo Cashback",readonly=True)
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
        ('10','10')],default="1")
    nilai_claim = fields.Float(string="Nilai Cashback",readonly=True)
    sisa_cashback = fields.Float(string="Sisa Cashback",readonly=True)

    @api.depends('amount_total')
    def _compute_maxcashback(self):
        for rec in self:
            rec.max_cashback = 10 * (rec.amount_total /100) 

   

    def btn_claim_cashback(self):
        if self.sisa_cashback < 0 :
            raise UserError(_('Saldo Cashback Tidak Mencukupi'))
        account_id = self.env['account.move'].browse(self._context.get('active_id'))
        mcc_id = self.env['master.customer.cashback'].browse(self._context.get('mcc_id'))
        if mcc_id:
            if mcc_id.state != 'confirm':
                raise UserError(_('Tidak Memiliki Master Customer Cashback Yang Running'))
        # account_id.cashback_percent = float(self.persent_cashback)
        # account_id.invoice_line_ids._onchange_price_subtotal()
        for rec in account_id.line_ids.filtered(lambda x:x.product_id.is_discount == False):
            # rec.cashback_percent = int(self.persent_cashback)
            rec._onchange_price_subtotal()
            rec.write({'cashback_percent':float(self.persent_cashback)})
            # rec.write({'cashback_percent':float(self.persent_cashback)})
            # rec.update(rec._get_price_total_and_subtotal())
            # rec.update(rec._get_fields_onchange_subtotal())
            # rec._onchange_price_subtotal()
        account_id.write({'cashback_total':self.nilai_claim})
        sequence_name = self.env['ir.sequence'].next_by_code('cashback.used.lines')
        self.env['cashback.used.lines'].create({
            'name':sequence_name,
            'date':fields.date.today(),
            'value':self.nilai_claim,
            'cashback_id': mcc_id.id,
            'account_id':account_id.id,
            'default_posting':'credit',
            'reference':'Cashback Used In ' + account_id.display_name,
            'state':'approve',
            'user_id':self.env.user.id,
        })
        self.env['cashback.lines'].create({
            'name':sequence_name,
            'group_id':mcc_id.group_id.id,
            'reference': 'Cashback Used In ' + account_id.display_name  ,
            'cashback_id': mcc_id.id,
            'cashback_rule':'Cashback Used',
            'account_id':account_id.id,
            'date': fields.date.today(),
            'value': self.nilai_claim,
            'default_posting':'credit',
            'state': 'approve',
            # 'cashback_rule_id': [(6, 0, line_id)],
        })
        return account_id


    @api.onchange('persent_cashback')
    def onchange_saldo_cashback(self):
        self.nilai_claim =  int(self.persent_cashback) * (self.amount_total / 100)
        self.sisa_cashback = self.saldo_cashback - self.nilai_claim
        