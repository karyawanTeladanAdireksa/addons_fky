# -*- coding: utf-8 -*-
{
    'name': "Aos BackOrder Expiry",

    'summary': """
        Aos BackOrder Expiry""",

    'description': """
        Aos BackOrder Expiry
    """,

    'author': "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'category': 'Stock',
    'version': '15.0.0.1.0',
    'depends': ['contacts',
                'stock',
                'aos_cashback'
            ],
    'data': [
        'data/ir_cron.xml',
        'views/partner_view.xml',
        'views/stock_picking.xml',
    ],

    "installable": True,
    "auto_install": False,
    "application": False,
}
