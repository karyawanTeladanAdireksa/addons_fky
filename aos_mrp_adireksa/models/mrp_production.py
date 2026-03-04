from odoo import api, fields, models, tools
import datetime

class MrpProduction(models.Model):
    _inherit = "mrp.production"
  

    date_planned_show = fields.Date(compute="compute_planned_show")

    @api.depends('date_planned_start')
    def compute_planned_show(self):
        for rec in self:
            rec.date_planned_show = rec.date_planned_start
    

                    


                    
                
    

        
        
                

        
    
            
    
    