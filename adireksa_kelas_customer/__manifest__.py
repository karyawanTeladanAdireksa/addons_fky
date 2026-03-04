# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Kelas Customer',
    'version': '15.0',
    'category': 'Partner',
    'sequence': 10,
    'summary': '',
    'description': '''
    Adding new field kelas in res.partner and product.pricelist
    ''',
    'website': 'http://www.alphasoft.id',
    'author': 'ALPHASOFT',
    'depends': ['product', 'purchase', 'sale', 'stock','contacts',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_class_view.xml',
        'views/res_partner_view.xml',
        'views/product_pricelist_view.xml',

        # 'views/product_view.xml',
        # # 'views/sr_purchase_multi_product_selection_views.xml',
        # 'views/sale_order_line.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}