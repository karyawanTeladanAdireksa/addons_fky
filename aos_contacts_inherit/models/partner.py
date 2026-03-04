# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class ResPartner(models.Model):    
    _inherit = "res.partner"
    
    # contact_person = fields.Many2one('res.users',string="Contact Person")
    contact_person = fields.Char(string="Contact Person", required=False, )
    def _avatar_get_placeholder_path(self):
        res = super(ResPartner,self)._avatar_get_placeholder_path()
        if self.type == 'delivery':
            return "aos_contacts_inherit/static/img/location.png"
        return res
    # def _avatar_get_placeholder_path(self):
    #     if self.is_company:
    #         return "base/static/img/company_image.png"
    #     if self.type == 'delivery':
    #         return "aos_contacts_inherit/static/img/location.png"
    #     if self.type == 'invoice':
    #         return "base/static/img/money.png"
    #     return super()._avatar_get_placeholder_path()