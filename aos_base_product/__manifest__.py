# -*- coding: utf-8 -*-
{
    'name': 'Aos Base Product',
    'version': '1.0',
    'category': 'Partner',
    'sequence': 10,
    'summary': '',
    'description': '''
    Hide Action Duplicate
    ''',
    'website': 'http://www.dev.com/',
    'author': 'dev/Alphasoft',
    'depends': ['product','sale', 'stock','purchase',],

    'data': [
       'views/hide_action_duplicate.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}