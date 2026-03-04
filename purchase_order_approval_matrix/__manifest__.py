# -*- coding: utf-8 -*-
{
    'name': 'Purchase Order Approval Matrix',
    'summary': """
        Purchase Order Approval Matrix""",
    'version': '15.0.0.1.0',
    'category': '',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'description': """
        author : Alphasoft \n
        Purchase Order Approval Matrix
    """,
    'depends': [
        'purchase',
        'approval_matrix',
    ],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,   
}