# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Invoice Print",
    'summary': """
        Invoice Print improvement.
        """,
    'description': """
        - Invoice Print Out will be adjusted to show:
            1. Logo PT shown
            2. Remove decimal in invoice
            3. Limit print 30 lines per pages
            4. Unlimited Invoice Lines, auto split to multiple pages
            5. Show page of pages.
    """,
    'author': 'Steven Adiputra',
    'category': 'Invoicing',
    'sequence': 99,
    'version': '15.0.0.1',
    'depends': ['base','mail','adireksa_invoice_slip','account'],
    'data': [
         'reports/report_actions.xml',
         'reports/reports_invoice_adireksa.xml',
         'reports/reports_invoice_adireksa_copy.xml',
    ],
    'installable': True,
    'application': True,
}
