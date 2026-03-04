# -*- coding: utf-8 -*-
{
    'name': "Aos - Stock Notification",
    'summary': """Stock Notification based on monthly and annual sales""",
    'description': """
        Notify certain Users in Dashboard for : Trigger excess =
        Quantity stock > past 12 month sales
        Trigger re-order =
        Quantity stock < past 3 month sales
    """,
    'author': 'Alphasoft',
    'category': 'Inventory',
    'sequence': 16,
    'version': '15.0.0.1',
    'depends': ['stock_account','purchase','product','sale','aos_product_adireksa', 'aos_product_outstanding'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'security/notify_stock_security.xml',
        'views/product_template.xml',
        'views/res_config_setting.xml',
        'views/stock_view.xml',
    ],
    'installable': True,
    'application': True,
}
