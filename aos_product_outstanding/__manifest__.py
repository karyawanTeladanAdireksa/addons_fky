# -*- coding: utf-8 -*-
{
    'name': 'Product Outstanding',
    'version': '15.0.0.1',
    'category': 'Stock',
    'summary': """Product Outstanding
        display total qty receipt moves
    """,
    'description': '''
            Product Outstanding
            display total qty receipt moves
    ''',
    'website': 'https://alphasoft.co.id',
    'author': 'Alphasoft',
    'depends': ['base',
                'purchase',
    ],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}