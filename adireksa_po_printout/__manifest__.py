# -*- coding: utf-8 -*-
{
    'name': 'Adireksa PO PrintOut',
    'version': '1.1.1',
    'category': 'purchase',
    'sequence': 10,
    'summary': '',
    'description': '''
    Adireksa PO PrintOut.
    ''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Lokesh - AntsyZ',
    'depends': ['purchase','aos_product_adireksa',],
    'data': [
        'report/confirmation_rfq_template.xml',
        'report/report_actions.xml'
        ],
        'installable': True,
        'application': True,
    }