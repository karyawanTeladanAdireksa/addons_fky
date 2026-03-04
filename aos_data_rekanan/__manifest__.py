# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Modul for Master Data Rekanan',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'summary': 'Modul for Master Data Rekanan',
    'sequence': 1,
    "author": "Alphasoft",
    'description': """
- Ceklist Is Suppliers & Is Customers
- Approval Matrix Supplier & Customers Creation
- Filter Customer in Sales & Vendor in Purchase
====================
    """,
    'category' : 'Tools',
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'depends' : [
        'base',
        'account',
        'purchase',
        'aos_contacts_approval_matrix',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/partner.xml',
        'views/tenant_document.xml',
        'views/document_template.xml',
    ],
    'demo': [],
    'test': [],
    'qweb': [],
    'css': [],
    'js': [],
    'price': 15.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
