# -*- coding: utf-8 -*-
{
    "name": "Sales Return",
    "summary": """
        Sales Return """,
    "description": """
        Sales Return
    """,
    "author": "Alphasoft",
    "website": "https://www.alphasoft.co.id/",
    "category": "stock",
    "version": "15.0.0.1.1",

    'depends': ['sale','stock','mail','product','aos_product_adireksa'],

    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'reports/sales_return_report_view.xml', 
        'wizard/replacement_product_view.xml',
        'views/action_view.xml',
        'views/sales_return_view.xml', 
        'views/stock_views.xml'
    ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": False,
    'license': 'LGPL-3',
}
