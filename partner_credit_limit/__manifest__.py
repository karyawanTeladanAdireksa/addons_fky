# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Credit Limit',
    'version': '1.1.1',
    'category': 'Partner',
    'depends': ['account', 'sale'],
    'license': 'AGPL-3',
    'author': 'Tiny, Serpent Consulting Services Pvt. Ltd./Jaydeep',
    'description': '''Partner Credit Limit'
        Checks for all over due payment and already paid amount
        if the difference is positive and acceptable then Salesman
        able to confirm SO
    ''',
    'website': 'http://www.serpentcs.com',
    'data': [
        'views/partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
