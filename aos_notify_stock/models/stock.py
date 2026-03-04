# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError,ValidationError


class ProductTempate(models.Model):
    _inherit = 'product.template'

    notify_stock = fields.Boolean(string='Notify Stock?', default=True)


class StockNotification(models.Model):
    _name = 'stock.notification'
    _description = 'Adireksa Stock Notification'

    name = fields.Char(string='Name')
    type = fields.Selection([('excess','Excess'),('reorder','Re-order')], string='Notification Type')
    user_id = fields.Many2one('res.users', string='Responsible')

    # def cron_stock_notification(self):
    #     cr = self.env.cr
    #     data = []
    #     cr.execute("""SELECT pp.id as product_id, pt.default_code, pt.name as product_name, 
    #         (select coalesce(sum(sq.qty),0) from stock_quant sq
    #         inner join stock_location sl1 on sl1.id = sq.location_id 
    #         where sl1.name = 'Stock' and sq.product_id = pp.id) as qty_on_hand,
    #         (select coalesce(sum(ail.quantity),0) from account_invoice ai
    #         inner join account_invoice_line ail on ail.invoice_id = ai.id
    #         where ail.product_id = pp.id and ai.state in ('open','paid') 
    #         and ai.date_invoice  between (NOW()::date - interval '3 month') and NOW()::date) as qty_sales_3_bulan,
    #         (select coalesce(sum(ail.quantity),0) from account_invoice ai
    #         inner join account_invoice_line ail on ail.invoice_id = ai.id
    #         where ail.product_id = pp.id and ai.state in ('open','paid') 
    #         and ai.date_invoice between (NOW()::date - interval '1 year') and NOW()::date) as qty_sales_setahun,
    #         (select coalesce(sum(case when cr.type='nonppn' then crl.scrap_qty else crl.good_qty end),0) as qty 
    #         from customer_return cr
    #         inner join customer_return_line crl on crl.return_id = cr.id
    #         where ((crl.type='ppn' and crl.product_id = pp.id) or (cr.type='nonppn' and crl.new_product_id = pp.id)) 
    #         and cr.state in ('approve','validate') 
    #         and cr.date_return between (NOW()::date - interval '3 month') and NOW()::date) as qty_cr_3_bulan,
    #         (select coalesce(sum(case when cr.type='nonppn' then crl.scrap_qty else crl.good_qty end),0) as qty 
    #         from customer_return cr
    #         inner join customer_return_line crl on crl.return_id = cr.id
    #         where ((crl.type='ppn' and crl.product_id = pp.id) or (cr.type='nonppn' and crl.new_product_id = pp.id)) 
    #         and cr.state in ('approve','validate') 
    #         and cr.date_return between (NOW()::date - interval '1 year') and NOW()::date) as qty_cr_setahun 
    #         from product_product pp
    #         inner join product_template pt on pt.id = pp.product_tmpl_id 
    #         where pt.notify_stock and pt.type in ('consu', 'product') and pp.active and pt.active
    #         and pt.default_code is not null order by pt.default_code""")
    #     res = cr.dictfetchall()
    #     if res:
    #         for rs in res:
    #             qty_sales_3_bulan = rs['qty_sales_3_bulan'] - rs['qty_cr_3_bulan']
    #             qty_sales_setahun = rs['qty_sales_setahun'] - rs['qty_cr_setahun']
    #             if rs['qty_on_hand'] > qty_sales_setahun: # Trigger excess
    #                 cr.execute("""SELECT user_id FROM stock_notification WHERE type='excess'""")
    #                 rec = cr.dictfetchall()
    #                 if rec:
    #                     for rc in rec:
    #                         data.append({
    #                             'type': 'excess',
    #                             'product': '[%s] %s' %(rs['default_code'], rs['product_name']),
    #                             'user_id': rc['user_id'],
    #                         })
    #             elif rs['qty_on_hand'] < qty_sales_3_bulan: # Trigger re-order
    #                 cr.execute("""SELECT type, user_id FROM stock_notification WHERE type='reorder'""")
    #                 rec = cr.dictfetchall()
    #                 if rec:
    #                     for rc in rec:
    #                         data.append({
    #                             'type': 'reorder',
    #                             'product': '[%s] %s' %(rs['default_code'], rs['product_name']),
    #                             'user_id': rc['user_id'],
    #                         })
    #     # Create notification to the responsible user
    #     if data:
    #         data = sorted(data, key = itemgetter('user_id'))
    #         for key, value in groupby(data, key = itemgetter('user_id')):
    #             for k in value:
    #                 if k['user_id'] == key:
    #                     return True
    #     return True