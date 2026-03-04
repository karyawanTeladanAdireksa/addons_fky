# -*- coding: utf-8 -*-
{
    'name': 'Contact Approval Matrix',
    'summary': """
        Contact Approval Matrix""",
    'version': '15.0.0.1.0',
    'category': '',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'description': """
        author : Alphasoft \n
        Contact Approval Matrix
    """,
    'depends': [
        'base',
        'contacts',
        'approval_matrix',
    ],
    'data': [
        'security/data_security.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,   
}