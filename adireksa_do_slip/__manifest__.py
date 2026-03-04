# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Delivery Slip',
    'version': '1.0',
    'category': 'stock',
    'sequence': 10,
    'summary': '',
    'description': '''
    Delivery Slip modifier.
    ''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Balaji - AntsyZ',
    'depends': ['stock'],
    'data': [
        'report/paper_a4_narrow_margin_top.xml',
        'report/delivery_slip.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}