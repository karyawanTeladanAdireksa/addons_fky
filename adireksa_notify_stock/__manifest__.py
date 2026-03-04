# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Stock Notification",
    'summary': """Stock Notification based on monthly and annual sales""",
    'description': """
        Notify certain Users in Dashboard for : Trigger excess =
        Quantity stock > past 12 month sales
        Trigger re-order =
        Quantity stock < past 3 month sales
    """,
    'author': 'Steven Adiputra',
    'category': 'Inventory',
    'sequence': 16,
    'version': '10.0.0.1',
    'depends': ['stock_account','adireksa_customer_return'],
    'data': [
        'security/ir.model.access.csv',
        'security/notify_stock_security.xml',
        'views/stock_view.xml',
    ],
    'installable': True,
    'application': True,
}
