# -*- coding: utf-8 -*-
{
    'name': 'Sales Return Approval',
    'summary': """
        Sales Return Approval""",
    'version': '15.0.0.1.0',
    'category': '',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'description': """
        author : Alphasoft \n
        Sales Return Approval
    """,
    'depends': [
        'aos_sales_return',
        'approval_matrix',
    ],
    'data': [
        'views/sales_return_approval_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,   
}