# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

{
    'name': 'Print Dynamic Barcode Labels',
    "version": "1.1.1",
    'author': 'TidyWay',
    'category': 'product',
    'website': 'http://www.tidyway.in',
    'summary': 'Print Labels from Inventory Product',
    'description': '''Print Dynamic Barcode Labels Mini''',
    'depends': ['base','stock','product'],
    'data': [
            'security/ir.model.access.csv',
            'wizard/dynamic_label_wizard.xml',
            'reports/action_report_barcode.xml',
            'reports/product_barcode_template.xml',
            'reports/product_barcode_template_mini.xml',
             ],
    'price': 99,
    'currency': 'EUR',
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['images/label.jpg'],
    'live_test_url': 'https://youtu.be/SPQZ8p7ATN4'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
