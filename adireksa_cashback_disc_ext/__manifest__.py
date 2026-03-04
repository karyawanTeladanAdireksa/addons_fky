# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Cashback/Discount Fix",
    'summary': """
        Fix Cashback and discount problems.
        """,
    'description': """
        - Fix interaction between cashback and discount module.
        - Fix bug in Invoice, sometimes the discount value is not calculated.
    """,
    'author': 'Steven Adiputra',
    'category': 'Sale',
    'sequence': 99,
    'version': '10.0.0.1',
    'depends': ['adireksa_cashback','sale'],
    'data': [],
    'installable': True,
    'application': True,
}
