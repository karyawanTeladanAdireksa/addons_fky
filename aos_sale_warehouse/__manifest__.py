# -*- coding: utf-8 -*-
{
    "name": "AOS Sale Warehouse",
    "summary": """
        Sale Warehouse""",
    "description": """
         Module for Sale Warehouse
    """,
    "author": "Alphasoft",
    "website": "https://www.alphasoft.co.id/",
    "category": "tools",
    "version": "15.0.0.1.1",

    'depends': ['sale','stock'],

    'data': [
        'views/sale_order.xml',
        'views/stock_move.xml',
        'views/stock_warehouse.xml',
        ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
