from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError
import ast

class ResPartner(models.Model):
    _inherit = "res.partner"

    expiry_count = fields.Integer(string="Expiry After")
    expiry_bool = fields.Boolean(string="Is Expiry")
