from odoo import fields, models, api, _


class Cashback(models.Model):
    _name = 'adireksa.cashback'
    _description = "CashBack"

    name = fields.Char(string="Cashback Name", required=True)
    kelas_customer = fields.Selection(
        [('blue', 'Blue (Annapurna)'),
         ('platinum', 'Platinum'),
         ('gold', 'Gold'),
         ('silver', 'Silver'),
         ('kelas_1_2', 'Kelas 2 & Kelas 1')],
        string='Kelas Customer')
    jenis_omset = fields.Selection([('bulanan', 'Bulanan'), ('quarter', 'Quarter'), ('annual', 'Annual')],
                                   string="Jenis Omset", required=True)
    jenis_cashback = fields.Selection([('bulanan', 'Bulanan'), ('quarterly', 'Quarterly'), ('annual', 'Annual'),
                                       ('pelunasan', 'Pelunasan'), ('promo', 'Promo')], string="Jenis Cashback", required=True)
    period_start = fields.Date(string="Period Start Date", default=fields.Datetime.now)
    period_end = fields.Date(string="Period End Date", default=fields.Datetime.now)
    aktifkan_cashback = fields.Boolean(string="Aktifkan Cashback")
    cashback_formula = fields.Integer(string="Cashback Formula(%)")
    state = fields.Selection([('draft', 'Draft'),
                              ('request_to_approval', 'Request For Approval'),
                              ('approved', 'Approved')], string="State", default="draft")

    def action_request_to_approve(self):
        self.write({'state': 'request_to_approval'})
        return True

    def action_approve(self):
        self.write({'state': 'approved'})
        return True

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        return True