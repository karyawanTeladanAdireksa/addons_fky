# -*- coding: utf-8 -*-
{
    'name': "Account Invoice Pivot & Graph",

    'summary': """
        Account Invoice Pivot & Graph""",

    'description': """
        Account Invoice Pivot & Graph
    """,

    'author': "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'category': 'Account',
    'version': '15.0.0.1.0',
    'depends': ['base',
                'account','aos_account_voucher','aos_cashback','aos_account_coupon'
            ],
    'data': [
        'security/security_view.xml',
        'views/account_move.xml',
        'views/account_voucher.xml',
    ],

    "installable": True,
    "auto_install": False,
    "application": False,
}
