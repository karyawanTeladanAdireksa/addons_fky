# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api, _
import odoo.addons.decimal_precision as dp


class StockNotifyReport(models.Model):
    _name = 'stock.notify.report'
    _description = 'Stock Excess or Reorder Detailed Report'
    _auto = False

    name = fields.Char(string='Name')
    product_id = fields.Many2one('product.template', string='Product')
    notify_stock = fields.Boolean(string='Notify Stock?')
    categ_id = fields.Many2one('internal.category', string='Internal Category')
    default_code = fields.Char(string='Internal Reference')
    jenis_motor = fields.Char(string='Tipe Motor')
    #company_id = fields.Many2one('res.company', string="Company", default=lambda s: s.env.company, required=True)
    barcode = fields.Char(string='Barcode')
    brand_id = fields.Many2one('product.brand',string='Brand')
    part_number = fields.Char(string='Part Number')
    internal_reference = fields.Char(string='Internal Reference')
    qty_on_hand = fields.Integer(string='On hand Quantity')
    qty_period = fields.Integer(string="Qty Periode (Dalam Bulan)")
    incoming_qty = fields.Integer(string='Incoming Quantity')
    # qty_sale_reorder = fields.Integer(string='Qty Sales 3 Bulan')
    # qty_sale_excess = fields.Integer(string='Qty Sales Setahun')
    qty_sales = fields.Integer(string='Qty Sales')
    status = fields.Selection([('normal','Normal'),('excess','Excess'),('reorder','Re-order')], 
        string='Status', default='normal')
    company_id = fields.Many2one('res.company', 'Company')


    def init(self):
        vendorLocation = self.env.ref('stock.stock_location_suppliers', raise_if_not_found=False)
        tools.drop_view_if_exists(self.env.cr, 'stock_notify_report')
        self.env.cr.execute("""CREATE VIEW stock_notify_report AS (
            SELECT stock.product_id as id,
                stock.name,
                stock.default_code,
                stock.notify_stock,
                stock.product_id,
                stock.company_id,
                stock.internal_reference,
                stock.barcode,
                stock.brand_id,
                stock.part_number,
                stock.categ_id,
                stock.qty_on_hand,
                stock.status,
                stock.qty_sales,
                stock.qty_period,
                stock.incoming_qty,
                stock.jenis_motor
                    FROM (
                        WITH locations AS (SELECT * FROM stock_location)
                        
                        SELECT prodk_tmpl.name as name,
                        prodk_tmpl.default_code as default_code,
                        prodk_tmpl.id as product_id,
                        prodk_tmpl.notify_stock as notify_stock,
                        prdk.barcode as barcode,
                        prodk_tmpl.default_code as internal_reference,
                        prdk_cat.id as categ_id,
                        prodk_tmpl.qty_on_hand_query as qty_on_hand,
                        prodk_tmpl.status as status,
                        prodk_tmpl.part_number as part_number,
                        prodk_tmpl.sales_qty_count as qty_sales,
                        --prodk_tmpl.incoming_qty as incoming_qty,
                        prodk_tmpl.sale_per_month as qty_period,
                        prodk_brnd.id as brand_id,
                        prodk_tmpl.company_id as company_id,
                        (SELECT SUM(moves.product_uom_qty) FROM stock_move moves
                            LEFT JOIN stock_picking picking ON picking.id = moves.picking_id
                            WHERE moves.product_id IN (SELECT moves_product.id 
                                                        FROM product_product moves_product 
                                                        WHERE moves_product.product_tmpl_id = prodk_tmpl.id)
                                AND moves.location_id IN (SELECT id FROM locations WHERE id = %s AND usage NOT IN ('internal', 'transit'))
                                AND moves.state = 'assigned'
                                AND moves.location_dest_id IN (SELECT id FROM locations WHERE usage IN ('internal', 'transit'))
                                AND moves.company_id = prodk_tmpl.company_id
                                AND picking.state != 'cancel'
                        ) AS incoming_qty,
                        
                        (SELECT array_to_string(array_agg(type.name),'/') from product_template_type_motor_rel product_type_rel left join type_motor type on type.id = product_type_rel.type_motor_id where product_type_rel.product_template_id = prodk_tmpl.id ) as jenis_motor
                        FROM product_template prodk_tmpl
                        LEFT JOIN internal_category prdk_cat ON prodk_tmpl.internal_category = prdk_cat.id
                        LEFT JOIN product_product prdk ON prdk.product_tmpl_id = prodk_tmpl.id
                        LEFT JOIN product_brand as prodk_brnd ON prodk_tmpl.product_brand = prodk_brnd.id
                        WHERE prodk_tmpl.active IS true AND prodk_tmpl.notify_stock IS true
                        ) stock  
            )    
           """, [vendorLocation.id])
        
