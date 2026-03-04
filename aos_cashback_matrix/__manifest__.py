# -*- coding: utf-8 -*-
{
    'name': 'Aos Cashback Approval Matrix',
    'summary': """
        Aos Cashback Approval Matrix""",
    'version': '15.0.0.1.0',
    'category': '',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'description': """
        author : Alphasoft \n
        Aos Cashback Approval Matrix
    """,
    'depends': [
        'aos_cashback',
        'approval_matrix',
    ],
    'data': [
        'views/customer_target.xml',
        'views/cashback_manual.xml',
        'views/cashback_rules.xml',
        'views/cashback_product.xml',
        'views/cashback_internal_category.xml',
        'views/cashback_internal_category_class.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,   
}