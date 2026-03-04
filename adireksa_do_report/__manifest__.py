# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Delivery Order Report",
    'summary': """
        Print Out Delivery order
        """,
    'description': """
        Print Out Surat Jalan add Qty / dus and Show Product name, not Product Template name which contains code.
    """,
    'author': 'Steven Adiputra',
    'category': 'Sales',
    'version': '10.0.0.1',
    'depends': ['adireksa_do_slip','stock','aos_product_adireksa',],
    'data': [
        'report/report_do_inherit.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': True,
}
