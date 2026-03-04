# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Credit Limit",
    'summary': """
        Patch to fix adireksa piutang and credit limit
        """,
    'description': """
        Fix bug for Piutang can be minus when confirming Sales and condition is over credit limit.
    """,
    'author': 'Steven Adiputra',
    'category': 'Sales',
    'version': '10.0.0.1',
    'sequence': 99,
    'depends': ['sale','partner_credit_limit'],
    'data': [],
    'installable': True,
    'application': True,
}
