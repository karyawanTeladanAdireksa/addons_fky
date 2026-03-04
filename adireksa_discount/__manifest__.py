# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Discount',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 12,
    'summary': 'Adding discount features in Sales Flow',
    'description': ''' This module will create new Menu for creating different type of discounts for sale order''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/ Vadivel Duraisamy',
    'depends': ['sale', 'adireksa_kelas_customer', 'sales_team', 'account', 
                # 'branch', 
                #'adireksa_sales_request'
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_discount.xml',
        'views/sale.xml',
        'views/account_invoice.xml',
        'views/sale_config_setting_views.xml',
        'security/security_view.xml',
        # 'views/templates.xml'
    ],
    'qweb': [
        "static/src/xml/discount_info.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}