from odoo import models, fields, api, _

class CustomerClass(models.Model):
	_name = 'customer.class'

	name = fields.Char(
	    string='Name',
	)
