from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get_year(self):
        return fields.date.today().year
    
    year = fields.Float(default=default_get_year)
    group_id = fields.Many2one(comodel_name="adireksa.customer.target", string="Customer Group", required=False)
    area_id = fields.Many2one(comodel_name="customer.area", string="Group Area", required=False, related='group_id.area_id')
    group_class_id = fields.Many2one('cashback.class.group',string="Group Class",related='group_id.group_class_id')
    def action_approved(self):
        res = super(ResPartner,self).action_approved()
        val = []
        for rec in self :
            val.append((0,0,{
                'partner_id':rec.id
            }))
        self.group_id.write({'partner_line_ids':val})
        return res
    
    def _action_set_group_target(self):
        partner_obj = self.env['res.partner'].search([])
        for rec in partner_obj:
            val = []
            val.append((0,0,{
                'partner_id':rec.id
            }))
            rec.group_id.write({'partner_line_ids':val})
        return