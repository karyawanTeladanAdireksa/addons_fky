# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Cashback Modifier',
    'version': '1.2',
    'category': 'Accounting',
    'sequence': 10,
    'summary': 'Modified Customer Cashback for Invoice and Sale Order',
    'description': '''
            V 1.0
            	- Hide Cashback Value, Cashback Per, Max Cashback field from SO
            V 1.1
                - When the invoice status is paid, the status of the pending cashback transaction summary Sales Order (out) should be approved, because the invoice for the Sales Order has already made a register payment
                - cashback customer is Manual or Auto :  When the cashback invoice is entered and the document is validate and the status is open, it will add cashback data to the cashback transaction summary with the type Customer Invoice (out) and Pending status. And after the customer invoice is paid, the pending status changes to approve
            V 1.2
                - 1. MCC Transaction Manual
                    - When a cashback transaction summary status is approved, the value of the pending is entered into the value in the cashback in field
                - 2 MCC Cashback Transaction Manual
                    - When master Customer > Cashback Generate Manual, when doing a manual cashback transaction, there will be an additional type, namely Customer Invoice (Used) with Manual Cashback = True and Default Posting = Credit and the value will be entered into the Cashback Used field.
            V 1.3
                - Changes related to module customer_cashback v 1.5.3
            V 1.4
                - Cashback readonly on non draft invoices

    ''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/MissK',
    'depends': ['customer_cashback','adireksa_discount'],
    'data': [
        # 'views/sale_order_view.xml',
        'views/account_invoice_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}