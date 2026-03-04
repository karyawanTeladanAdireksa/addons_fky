from odoo import models,fields,api,_

class ActionType(models.Model):
    _name = "res.action.type"
    _description = "Sales Return Action Type"

    name = fields.Char(string="Description")

    # Action Type
    is_receipt = fields.Boolean(string="Is receipt",help="Tipe Aksi untuk menerima produk ke gudang")
    is_delivery = fields.Boolean(string="Is Delivery",help="Tipe Aksi untuk mengembalikan ke pelanggan")
    is_replacement = fields.Boolean(string="Is Replacement",help="Tipe Aksi untuk penggantian produk")
    is_default_return = fields.Boolean(string="Is Default Return",help="Default Action Return")
    is_default_replacement = fields.Boolean(string="Is Default Replacement",help="Default Action Replacement")
    other_action = fields.Boolean(string="Other Action")


class ConditionProduct(models.Model):
    _name = "res.condition.product"
    _description = "Condition Product"

    name = fields.Char(string="Description")

