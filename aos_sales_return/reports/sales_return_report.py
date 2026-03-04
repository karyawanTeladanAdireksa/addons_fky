from odoo import models,fields,api
from odoo import tools

class SalesReturnReport(models.Model):
    _name = "sales.return.report"
    _description = "Sales Return Analysis Report"
    _auto = False
    _rec_name = "date"
    _order = "date desc"
    
    
    name = fields.Char(string="Number",readonly=True)
    partner_id = fields.Many2one('res.partner',string="Customer",readonly=True)
    document = fields.Char(string="Reference",)
    date = fields.Date(string="Date")
    state = fields.Selection([
                        ('draft','Draft'),
                        ('confirm','Confirm'),
                        ('incoming','Receipt'),
                        ('outgoing','Delivery'), 
                        ('done','Done'),
                        ('cancel','Cancel'),
                    ],string="State",readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",readonly=True)
    receipt_dest_location_id = fields.Many2one('stock.location',string="Receipt Destination Location",readonly=True)
    receipt_source_location_id = fields.Many2one('stock.location',string="Receipt Source Location", readonly=True)
    delivery_dest_location_id = fields.Many2one('stock.location',string="Delivery Destination Location", readonly=True)
    delivery_source_location_id = fields.Many2one('stock.location',string="Delivery Source Location",readonly=True )
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency',string="Currency", readonly=True)
    product_id = fields.Many2one('product.product',string="Product",readonly=True)
    condition_id = fields.Many2one('res.condition.product',string="Condition",readonly=True)
    qty = fields.Float(string="Qty",readonly=True)
    price_unit = fields.Float(string="Price Unit",readonly=True)
    price_subtotal = fields.Monetary(string="Price Total",currency_field="currency_id",readonly=True)
    replacement_product_id = fields.Many2one('product.product',string="Replacement Product",readonly=True)
    replacement_qty = fields.Float(string="Replacement Quantity",readonly=True)
    replacement_price_unit = fields.Float(string="Replacement Price Unit",readonly=True)
    replacement_subtotal = fields.Float(string="Replacement Total",readonly=True)
    user_id = fields.Many2one('res.users','Create By',readonly=True)
    return_id = fields.Many2one('sales.return', 'Sales Return #', readonly=True)

    
    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            r.partner_id as partner_id,
            r.name as name,
            r.document as document,
            r.date as date,
            r.state as state,
            r.warehouse_id as warehouse_id,
            r.receipt_dest_location_id as receipt_dest_location_id,
            r.receipt_source_location_id as receipt_source_location_id,
            r.delivery_dest_location_id as delivery_dest_location_id,
            r.delivery_source_location_id as delivery_source_location_id,
            r.company_id as company_id,
            r.currency_id as currency_id,
            r.create_uid as user_id,
            min(l.id) as id,
            l.product_id as product_id,
            l.qty as qty,
            l.price_unit as price_unit,
            l.price_subtotal as price_subtotal,
            l.return_id as return_id,
            l.condition_id as condition_id,
            rl.product_id as replacement_product_id,
            t.list_price as replacement_price_unit,
            rl.price_subtotal as replacement_subtotal,
            rl.qty as replacement_qty
        """
        for field in fields.values():
            select_ += field
        return select_
    
    def _from_sale(self, from_clause=''):
        from_ = """
                sales_return_line l
                      left join sales_return r on (r.id=l.return_id)
                      join res_partner partner  on r.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join replacement_product rl on (rl.return_line_id = l.id)
                %s
        """ % from_clause
        return from_
    
    def _group_by_sale(self, groupby=''):
        groupby_ = """
            l.product_id,
            l.return_id,
            t.id,
            t.uom_id,
            r.name,
            r.partner_id,
            r.state,
            r.company_id,
            r.id,
            l.id,
            rl.id %s
        """ % (groupby)
        return groupby_
    
    def _select_additional_fields(self, fields):
        """Hook to return additional fields SQL specification for select part of the table query.

        :param dict fields: additional fields info provided by _query overrides (old API), prefer overriding
            _select_additional_fields instead.
        :returns: mapping field -> SQL computation of the field
        :rtype: dict
        """
        return fields
    
    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        sale_return_report_fields = self._select_additional_fields(fields)
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return '%s (SELECT %s FROM %s GROUP BY %s)' % \
                (with_, self._select_sale(sale_return_report_fields), self._from_sale(from_clause), self._group_by_sale(groupby))
    
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))