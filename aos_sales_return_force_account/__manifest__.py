# -*- coding: utf-8 -*-
{
    "name": "Sales Return Stock Force Account",
    "summary": """
        Sales Return Stock Force Account""",
    "description": """
        Sales Return Stock Force Account
    """,
    "author": "Imronsyabani",
    "website": "",
    "category": "stock",
    "version": "15.0.0.1.1",

    'depends': ['aos_sales_return','aos_force_stock_account'],

    'data': [
        'views/sales_return_view.xml',
        ],
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": False,
}
