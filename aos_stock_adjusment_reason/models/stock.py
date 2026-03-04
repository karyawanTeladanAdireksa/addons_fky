from odoo import models,fields,api

class StockQuant(models.Model):
    _inherit = "stock.quant"
    
    reason = fields.Char(string="Reason")
    
    @api.model
    def _get_inventory_fields_create(self):
        fields = super(StockQuant,self)._get_inventory_fields_create()
        fields += ['reason']
        return fields
    
    @api.model
    def _get_inventory_fields_write(self):
        fields = super(StockQuant,self)._get_inventory_fields_write()
        fields += ['reason']
        return fields
    
    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super(StockQuant,self)._get_inventory_move_values(qty, location_id, location_dest_id, out)
        if not fields.Float.is_zero(qty, 0, precision_rounding=self.product_uom_id.rounding):
            res['name'] = res['name'] + (' - ' + self.reason if self.reason else '')
            res['reference'] = res['name'] + (' - ' + self.reason if self.reason else '')
            self.reason = ''
        return res
    
    def action_set_inventory_quantity_to_zero(self):
        super(StockQuant, self).action_set_inventory_quantity_to_zero()
        self.reason = False
    
    @api.model
    def create(self, vals):
        quant = super(StockQuant,self).create(vals)
        if vals.get('reason') and quant.reason != vals.get('reason'):
            quant.reason = vals.get('reason')
        return quant
    
    # def write(self,vals):
    #     res = super(StockQuant,self).write(vals)
    #     # Do nothing when user tries to modify manually a inventory loss. but we need to always update reason
    #     if self.location_id.usage == 'inventory':
    #         if vals.get('reason') != None:
    #             return super(StockQuant, self.with_context(inventory_mode=False)).write(vals)
    #     return res