# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Aged fr Due',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'summary': 'Aged fr Due & Aged Payment Due',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
Account Voucher
====================
    """,
    'category' : 'Tools',
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'depends' : ['account'],
    'data': [
        'views/account_move_views.xml',
    ],
    'demo': [],
    'test': [],
    'qweb': [],
    'css': [],
    'js': [],
    'price': 0.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
