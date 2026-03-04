# -*- coding: utf-8 -*-
{
    'name': 'Aos Product Pricelist',
    'version': '1.0',
    'category': 'Product',
    'sequence': 10,
    'summary': '',
    'description': '''
    Product Pricelist
    ''',
    'website': 'http://www.dev.com/',
    'author': 'Alphasoft',
    'depends': ['product','sale','account','aos_cashback'],

    'data': [
       'views/product_pricelist.xml',
       'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}