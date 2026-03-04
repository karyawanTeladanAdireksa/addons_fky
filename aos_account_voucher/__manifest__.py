# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Account Voucher',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'summary': 'Account Voucher Management',
    'sequence': 50,
    "author": "Alphasoft",
    'description': """
Account Voucher
====================
    """,
    'category' : 'Account Voucher Management',
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'depends' : ['account'],
    'data': [
        'security/account_voucher_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'report/account_voucher_report_view.xml',
        #'report/account_voucher.xml',
        'wizard/account_voucher_report_download.xml',
        'wizard/voucher_report_view.xml',
        'views/petty_cashbox_view.xml',
        'views/account_journal_view.xml',
        'views/account_voucher_view.xml',
        'views/menuitem_view.xml',
        'data/account_voucher_data.xml',
    ],
    'demo': [],
    'test': [],
    'qweb': [],
    'css': [],
    'js': [],
    'price': 65.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
    #'post_init_hook': '_auto_install_l10n',
}
