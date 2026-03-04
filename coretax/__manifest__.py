# -*- coding: utf-8 -*-
{
    'name': 'Coretax DJP',
    'summary': """
        - Generate Invoice XML & Xlsx Coretax DJP
    """,
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'category': 'Accounting',
    "author": "Alphasoft",
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'description': """
        author : Alphasoft \n
        Generate Invoice XML & Excel
    """,
    'depends': [
        'account',
        'l10n_id_efaktur',
    ],
    'data': [
        'data/ir_server.xml',
        'data/coretax.product.csv',
        'data/coretax.uom.csv',
        'data/res_country_data.xml',
        'security/ir.model.access.csv',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/account_move_view.xml',
        'views/cortex_view.xml',
        'views/res_config_settings_views.xml',
        'views/menuitem_view.xml',
    ],
    'price': 645.0,
    'currency': 'USD',
    'installable': True,
    'application': True,
    'auto_install': False
}
