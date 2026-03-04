# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Cust Receipt Modifier',
    'version': '1.0',
    'category': 'Report Customer Invoice',
    'sequence': 10,
    'summary': '',
    'description': '''
  Adding printout of invoices for customer receipt
    ''',
    'website': 'http://www.dev.com/',
    'author': 'dev/Alphasoft',
    'depends': ['base','account','aos_data_rekanan'],

    'data': [
       'security/ir.model.access.csv',
       'report/report_cust_invoice.xml',
       'report/report_actions.xml',
       'wizard/customer_invoice_wizard.xml',
      #  'wizard/customer_receipt_wizard.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}