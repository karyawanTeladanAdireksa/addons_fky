# -*- coding: utf-8 -*-
{
    'name': 'Product Creation Extended Module',
    'version': '15.0.0.1',
    'category': 'Security',
    'summary': """Product Creation Extended Module For Create Product With MRP Access Right""",
    'description': '''
            Product Creation Extended Module For Create Product With MRP Access Right
    ''',
    'website': 'https://alphasoft.co.id',
    'author': 'Alphasoft',
    'depends': ['aos_creation_product','mrp'],

    'data': [
        'security/ir.model.access.csv',
        'view/mrp_form_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}