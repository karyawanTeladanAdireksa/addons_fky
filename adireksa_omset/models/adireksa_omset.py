from odoo import models, fields, api


class Adireksaomset(models.Model):
    _name = "adireksa.omset"
    _description = "Customer Omset"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name Omset", required=True)
    jenis_omset = fields.Selection([('bulanan', 'Bulanan'), ('quarter', 'Quarter'), ('annual', 'Annual')],
                                   string="Jenis Omset", required=True)
    tahun = fields.Integer(string="Tahun")
    period_start = fields.Date(string="Period Start Date", default=fields.Datetime.now)
    period_end = fields.Date(string="Period End Date", default=fields.Datetime.now)
    aktifkan_omset = fields.Boolean(string="Aktifkan Omset")

    #Tree View #
    omset_lines = fields.One2many('omset.lines', 'omset_id', string="Omset Lines")


class OmsetLines(models.Model):
    _name = "omset.lines"

    omset_id = fields.Many2one('adireksa.omset', string="Customer Omset")
    partner_id = fields.Many2one('res.partner', string="Nama Customer")
    kelas_customer_ = fields.Selection(
        [('blue', 'Blue (Annapurna)'),
         ('platinum', 'Platinum'),
         ('gold', 'Gold'),
         ('silver', 'Silver'),
         ('kelas_1_2', 'Kelas 2 & Kelas 1')],
        string='Kelas Customer')
    kelas_customer_id = fields.Many2one(
        'customer.class',
        string='Kelas Customer',
    )
    target_omset = fields.Float(string="Target Omset")
    jenis_omset = fields.Selection(related="omset_id.jenis_omset", string="Jenis Omset")
    tahun = fields.Integer(related="omset_id.tahun", string="Tahun")
    period_start = fields.Date(related="omset_id.period_start", string="Period Start Date")
    period_end = fields.Date(related="omset_id.period_end", string="Period End Date")
    aktifkan_omset = fields.Boolean(related="omset_id.aktifkan_omset", string="Aktifkan Omset")


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.kelas_customer_id = self.partner_id.kelas_id
