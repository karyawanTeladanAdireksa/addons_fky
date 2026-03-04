# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Contacts Inherit',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'summary': 'Add Contact Person',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
Add Contact Person
    """,
    'category' : 'Partners',
    'website': 'https://www.alphasoft.co.id/',
    'images' : ['images/main_screenshot.png'],
    'depends' : ['contacts','base','aos_data_rekanan'],
    'data': [
        "views/partner_view.xml",
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'price' : 10,
    'currency' : 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
