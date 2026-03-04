from odoo import models,fields,api,_
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    @api.model
    def model_not_allowed_to_add_product(self):
        return ['purchase.order.line','sale.order.line','sales.return.line']
    
    # def write(self,vals):
    #     res = super(StockPicking,self).write(vals)
    #     # cause in state done move ids and move line is readonly
    #     if self.state in ('confirmed','assigned'):
    #         list_fields = list(filter(lambda item: self.move_ids_without_package._fields.get(item[0]).comodel_name in self.model_not_allowed_to_add_product() ,self.move_ids_without_package._fields.items()))
            
    #         if list_fields:
    #             for field in list_fields:   
    #                 # check if mix in moves from this picking add manually and from Purchase or Sale Order or Sales Return
    #                 if (self.move_ids_without_package.filtered(lambda move:move.__getattribute__(field[0])) and \
    #                     self.move_ids_without_package.filtered(lambda move: not move.__getattribute__(field[0]))):
    #                       self.move_ids_without_package.filtered(lambda move: not move.__getattribute__(field[0])).state = "draft"
    #                       raise UserError(_("You cannot add product manually to this transfer %s") % self.name)
                      
    #                 # check demand qty its not equal to quantity done
    #                 # if self.move_ids_without_package.filtered(lambda move: float_compare(move.product_uom_qty, move.quantity_done, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')) < 0):
    #                 #     raise UserError(_("You cannot add quantity done greater than quantity demand"))
    #     return res
    
    def button_validate(self):
        move_to_check = self.move_ids_without_package.filtered(lambda move: float_compare(move.product_uom_qty, move.quantity_done, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')) < 0)
        if move_to_check:
            raise UserError(_("You cannot add quantity done greater than quantity demand for product %s" % move_to_check[0].product_id.name))
        return super(StockPicking,self).button_validate()   