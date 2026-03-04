# -*- coding: utf-8 -*-
{
    "name": "AOS Stock Picking Batch",
    "summary": """
        Stock Picking Batch""",
    "description": """
         Module for Stock Picking Batch
    """,
    "author": "Alphasoft",
    "website": "https://www.alphasoft.co.id/",
    "category": "stock",
    "version": "15.0.0.1.1",

    'depends': ['contacts','aos_cashback','stock_picking_batch'],

    'data': [
        'views/stock_picking_batch.xml',
        ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
