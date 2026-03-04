# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Aos Mrp Adireksa',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'summary': 'Aos Mrp Adireksa by Alphasoft',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
        Aos Mrp Adireksa'
    """,
    'category' : 'Tools',
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'depends' : ['mrp'],
    'data': [
        'views/mrp_form_view.xml',
    ],
    'demo': [],
    'test': [],
    'qweb': [],
    'css': [],
    'js': [],
    'price': 10.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}