from odoo import models,api,fields,_
from odoo.exceptions import UserError
from odoo.tools import float_compare

class SalesOrder(models.Model):
    _inherit = "sale.order"

    area_id = fields.Many2one("customer.area", related="partner_id.group_id.area_id")
    group_id = fields.Many2one("adireksa.customer.target", string="Customer Group", related="partner_id.group_id")
    group_class_id = fields.Many2one("cashback.class.group", string="Cashback Class Group", related="partner_id.group_class_id")



class SaleReport(models.Model):
    _inherit = "sale.report"

    group_id = fields.Many2one("adireksa.customer.target", string="Customer Group", readonly=True)
    
    def _group_by_sale(self,groupby=''):
          res = super(SaleReport,self)._group_by_sale(groupby)
          res +=""",partner.group_id"""
          return res
    
    def _select_sale(self,fields=None):
         return super(SaleReport, self)._select_sale() + ", partner.group_id as group_id"
   