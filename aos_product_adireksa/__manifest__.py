# -*- coding: utf-8 -*-
{
    'name': 'Aos Product Adireksa',
    'version': '1.0',
    'category': 'Partner',
    'sequence': 10,
    'summary': '',
    'description': '''
    Adding new field in product.template
    ''',
    'website': 'http://www.dev.com/',
    'author': 'dev/Alphasoft',
    'depends': ['base','product','sale', 'stock','stock_account','purchase','account','l10n_id_efaktur'],

    'data': [
       'security/ir.model.access.csv',
       'security/security.xml',
       'data/ir_cron.xml',
       'views/ir_actions.xml',
       'views/view_product_adireksa.xml',
       'views/view_account_move.xml',
       'views/view_product_template.xml',
       'views/view_purchase_order.xml',
       'views/view_sale_order.xml',
       'views/view_stock.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}