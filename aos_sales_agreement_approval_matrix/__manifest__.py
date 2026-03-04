# -*- coding: utf-8 -*-
{
    'name': 'Sales Agreement Approval',
    'summary': """
        Sales Agreement Approval""",
    'version': '15.0.0.1.0',
    'category': '',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'description': """
        author : Alphasoft \n
        Sales Agreement Approval
    """,
    'depends': [
        'aos_sales_agreement',
        'approval_matrix',
    ],
    'data': [
        'views/sales_agreement_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,   
}