# -*- coding: utf-8 -*-
{
    'name': 'AOS Credit Limit Request Approval Matrix',
    'summary': """
        Credit Limit Request Approval Matrix""",
    'version': '15.0.0.1.0',
    'category': '',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'description': """
        author : Alphasoft \n
        Credit Limit Request Approval Matrix
    """,
    'depends': [
        'aos_credit_limit_request',
        'approval_matrix',
    ],
    'data': [
        'views/credit_limit_request_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,   
}