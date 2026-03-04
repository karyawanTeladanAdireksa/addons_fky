# -*- coding: utf-8 -*-
{
    "name": "AOS Credit Limit Request",
    "summary": """
        Credit Limit Request""",
    "description": """
        create new module for credit limit request
    """,
    "author": "Alphasoft",
    "website": "www.alphasoft.co.id",
    "category": "account",
    "version": "1.1.1",

    'depends': ['dev_customer_credit_limit','base','sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/credit_limit_request_view.xml',
        ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": True,
}
