from odoo import api, fields, models, _

class CustomerGroup(models.Model):
    _name = 'customer.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Customer Group'

    name = fields.Char(string="Group Name", required=False, )
    area_id = fields.Many2one(comodel_name="customer.area", string="Group Area", required=False, )
    partner_ids = fields.One2many(comodel_name="res.partner", inverse_name="group_id", string="", required=False, )
    # partner_ids = fields.Many2many(comodel_name="res.partner", relation="partner_id", column1="", column2="", string="", )


# class CustomerArea(models.Model):
#     _name = 'customer.area'
#     _rec_name = 'name'
#     _description = 'Customer Area'

#     name = fields.Char(string="", required=False, )
