# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Cashback Manual',
    'version': '1.0',
    'category': 'account',
    'sequence': 10,
    'description': 'Adireksa Cashback Manual.',
    'summary': '',
    'website': 'http://web.antsyz.com/',
    'author': 'Hashmicro/Antsyz-Lokesh',
    'depends': ['adireksa_cashback','sale'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/customer_cashback_views.xml',
        'views/account_views.xml',
    ],
    'installable': True,
    'application': True,
}