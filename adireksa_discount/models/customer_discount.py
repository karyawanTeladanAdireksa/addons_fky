from odoo import fields, models, api


class CusotmerDiscount(models.Model):
    _name = "adireksa.discount"
    _inherit = ['mail.thread']

    name = fields.Char(string="Nama Diskon", track_visibility='always')
    jenis_diskon = fields.Selection([('diskon_dasar', 'Discount Dasar'), ('diskon_quantity', 'Discount Quantity'), ('diskon_promo', 'Discount Promo'),
                                     ('diskon_ongkir', 'Discount Ongkir'), ('diskon_cash', 'Discount Cash')], required=True, string="Jenis Discount", track_visibility='always')
    master_discount_type_id = fields.Many2one(
        'master.discount.type',
        string='Diskon Type',
    )
    kelas_customer = fields.Selection(
        [('blue', 'Blue (Annapurna)'),
         ('platinum', 'Platinum'),
         ('gold', 'Gold'),
         ('silver', 'Silver'),
         ('kelas_1_2', 'Kelas Umum')],
        string='Kelas Customer', track_visibility='always')
    kelas_customer_id = fields.Many2one(
        'customer.class',
        string='Kelas Customer',
    )
    period_start = fields.Date(string="Period Start", track_visibility='always')
    period_end = fields.Date(string="Period End", track_visibility='always')
    aktifkan_diskon = fields.Boolean(string="Aktifkan Diskon", track_visibility='always')
    formula_diskon = fields.Float(string="Formula Discount(%)", track_visibility='always')
    state = fields.Selection([('draft', 'Draft'),
                              ('request_to_approval', 'Request For Approval'),
                              ('approved', 'Approved')], string="State", default="draft", track_visibility='always')

    def action_request_to_approve(self):
        self.write({'state': 'request_to_approval'})
        return True

    def action_approve(self):
        self.write({'state': 'approved'})
        return True

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        return True

class MasterDiscountType(models.Model):
    _name = 'master.discount.type'

    name = fields.Char(
        string='Name',
    )