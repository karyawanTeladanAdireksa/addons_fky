# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Invoice Slip',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 12,
    'summary': 'Invoice Slip design for Customer Invoice',
    'description': ''' This module will create new invoice Report in Customer Invoice Form''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/ Vadivel Duraisamy',
    'depends': ['account'],
    'data': [
        'report/views.xml',
        'report/invoice_slip_report.xml',
        'report/invoices.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}