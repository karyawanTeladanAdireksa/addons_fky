# -*- coding: utf-8 -*-
{
    "name": "Report Journal Voucher Adireksa",
    "summary": """
        Report Journal Voucher""",
    "description": """
        Report Journal Voucher
    """,
    "author": "ALPHASOFT",
    "website": "www.alphasoft.id",
    "category": "account",
    "version": "15.0.0",

    'depends': ['aos_account_voucher','account',],  

    'data': [
           'reports/report_actions.xml',
           'reports/report_journal_template.xml',
        ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": True,
}
