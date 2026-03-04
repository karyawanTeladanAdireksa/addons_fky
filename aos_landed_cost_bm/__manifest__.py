# -*- coding: utf-8 -*-
{
    'name': 'Aos Landed Cost BM',
    'version': '1.0',
    'category': 'Product',
    'sequence': 10,
    'summary': '',
    'description': '''
    Landed Cost BM
    ''',
    'website': 'http://www.dev.com/',
    'author': 'Alphasoft',
    'depends': ['product','stock_landed_costs'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/stock_landed_cost.xml',
        'views/account_move.xml',
        'wizard/vendor_bill_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}