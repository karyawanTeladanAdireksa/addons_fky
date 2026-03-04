# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Cashback Pattern",
    'summary': """
        Cashback pattern extension.
        """,
    'description': """
         Add Cashback Pattern Entry.
    """,
    'author': 'Steven Adiputra',
    'category': 'Sales',
    'sequence': 16,
    'version': '10.0.0.1',
    'depends': ['customer_cashback'],
    'data': [
        # 'report/cashback_report_template.xml',
        # 'wizard/cashback_print_view.xml',
        'security/cashback_pattern_security.xml',
        'security/ir.model.access.csv',
        'data/cashback_type_data.xml',
        'views/cashback_view.xml',
    ],
    'installable': True,
    'application': True,
}
