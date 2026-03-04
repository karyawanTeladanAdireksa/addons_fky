# -*- coding: utf-8 -*-
{
    'name': "Purchase Order BackOrder",

    'summary': """
        Purchase Order BackOrder""",

    'description': """
        Purchase Order BackOrder
    """,

    'author': "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'category': 'Purchase Order',
    'version': '15.0.0.1.0',
    'depends': ['base',
                'purchase',
                'purchase_stock'
            ],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'wizard/backorder_wizard.xml',
    ],

    "installable": True,
    "auto_install": False,
    "application": False,
}
