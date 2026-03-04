from odoo import models, fields, api
from odoo.osv import expression

class CoretaxUoM(models.Model):
    _name = "coretax.uom"
    _description = "Coretax UoM"
    _order = "id asc"
    
    @api.depends('code')
    def _compute_display_name(self):
        for uom in self:
            uom.display_name = f"{uom.code} - {uom.name}"

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Description", required=True)
    category = fields.Selection([('barang', 'Barang'), ('jasa', 'Jasa')], string="Kelompok", default="barang", required=True)

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            if operator in ('=', '!='):
                name_domain = ['|', ('code', '=', name.split(' ')[0]), ('name', operator, name)]
            else:
                name_domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                name_domain = ['&', '!'] + name_domain[1:]
            domain = expression.AND([name_domain, domain])
        return self._search(domain, limit=limit, order=order)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         vals['code'] = " ".join(vals['code'].split(" ")) if vals.get('code') else False
    #         vals['name'] = " ".join(vals['name'].split(" ")) if vals.get('name') else False
    #     return super(CoretaxUoM, self).create(vals_list)