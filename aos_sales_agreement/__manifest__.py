# -*- coding: utf-8 -*-
{
    "name": "Sales Agreemet",
    "summary": """
        Sales Agreement """,
    "description": """
        Sales Agreement
    """,
    "author": "syabani",
    "website": "https://www.alphasoft.co.id/",
    "category": "stock",
    "version": "15.0.0.1.1",

    'depends': ['base','sale','aos_cashback'],

    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'security/sale_agreement_security.xml',
        'views/sale_agreement_view.xml',
        'views/sale_agreement_line_view.xml',
        'views/sale_order_view.xml',
        'views/action.xml',
        'views/menuitem.xml',
        'wizard/make_to_sale_order_view.xml',
        ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": True,
}
