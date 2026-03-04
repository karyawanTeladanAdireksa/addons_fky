from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError
import ast
from datetime import datetime


class SelectMultiProduct(models.TransientModel):
	_name = 'select.multi.product'
	_description = 'add Multiple Product'

	product_ids = fields.Many2many('product.product', string='Products')
	flag_order = fields.Char('Flag Order')

	def select_products(self):
		if self.flag_order == 'so':
			order_id = self.env['sale.order'].browse(self._context.get('active_id', False))
			for product in self.product_ids:
				line = self.env['sale.order.line'].create({
					'product_id': product.id,
					'product_uom': product.uom_id.id,
					'price_unit': product.lst_price,
					'order_id': order_id.id,
				})
				line._onchange_discount()

		elif self.flag_order == 'po':
			order_id = self.env['purchase.order'].browse(self._context.get('active_id', False))
			for product in self.product_ids:
				if product.id in order_id.order_line.mapped('product_id').ids:
					raise UserError(_('%s is Duplicate') % product.display_name )
				self.env['purchase.order.line'].create({
					'product_id': product.id,
					'name': product.description_purchase,
					'date_planned': order_id.date_planned or datetime.today(),
					'product_uom': product.uom_id.id,
					'product_qty': 1.0,
					'display_type': False,
					'order_id': order_id.id,
					'product_brand':product.product_brand.id,
					'internal_category':product.internal_category.id,
					'part_number':product.part_number,
					'type_motor':product.type_motor.ids
				})