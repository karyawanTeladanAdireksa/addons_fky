from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class VendorBillWizard(models.TransientModel):
    _name = 'vendor.bill.wizard'
    _description = 'Vendor Bill Wizard'


    partner_id = fields.Many2one('res.partner',string="Vendor",required=True)

    cost_lines = fields.Many2many('stock.landed.cost.lines')
    cost_id = fields.Many2one('stock.landed.cost')

    def btn_create_vendor(self):
        journal_id = self.env['account.journal'].search([('name','=','Vendor Bills')])
        account_id = self.env['account.move'].create({
            'partner_id':self.partner_id.id,
            'group_id':self.partner_id.group_id.id,
            'area_id':self.partner_id.area_id.id,
            'journal_id':journal_id.id,
            'cost_id':self.cost_id.id,
            'move_type':'in_invoice',
            'invoice_line_ids':[(0, 0, {
                'product_id': self.cost_lines.product_id.id,
                'account_id':self.cost_lines.account_id.id,
                'quantity': self.cost_lines.qty,
                'price_unit':self.cost_lines.price_unit,
            })],
        })
        self.cost_id.write({'vendor_bill_id':account_id.id}) 
        return account_id
