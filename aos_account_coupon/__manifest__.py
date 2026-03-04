# -*- coding: utf-8 -*-
{
    'name': "Account Coupon",

    'summary': """
        Account Coupon""",

    'description': """
        Account Coupon
    """,

    'author': "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'category': 'Account',
    'version': '15.0.0.1.0',
    'depends': ['coupon', 'account','adireksa_invoice_print',],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_coupon_apply_code_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'views/coupon_program_views.xml',
        'views/coupon_views.xml',
        'reports/reports_invoice_adireksa.xml',
    ],

    "installable": True,
    "auto_install": False,
    "application": False,
}
