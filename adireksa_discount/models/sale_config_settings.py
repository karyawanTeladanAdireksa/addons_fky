from odoo import api, fields, models


class SaleConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    diskon_per_so_line_method = fields.Selection([
        ('0', 'No discount on sales order lines'),
        ('1', 'Allow discounts on sales order lines'),
        ('2', 'Allow Adireksa Discount Method')], "Discount",config_parameter="adireksa_discount.diskon_per_so_line_method",default="0",required=True)

    # group_diskon_per_so_line1 = fields.Selection([('0','A')])
    group_diskon_per_so_line1 = fields.Boolean(string="Adirksa Discount", implied_group='adireksa_discount.group_diskon_per_so_line1')

    @api.onchange('diskon_per_so_line_method')
    def _onchange_sale_price(self):
        if self.diskon_per_so_line_method == '0':
            self.update({'group_diskon_per_so_line1': False,'group_discount_per_so_line': False})
        elif self.diskon_per_so_line_method == '1':
            self.update({'group_diskon_per_so_line1': False,'group_discount_per_so_line': True})
        else:
            self.update({'group_diskon_per_so_line1': True, 'group_discount_per_so_line': False})


