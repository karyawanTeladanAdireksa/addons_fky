from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
     _inherit = "purchase.order"


     def print_quotation(self):
          self.write({'state': "sent"})
          return self.env.ref('adireksa_po_printout.action_report_purchase_order_quotation').report_action(self)