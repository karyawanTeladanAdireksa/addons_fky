# -*- coding: utf-8 -*-
{
    "name": "Cashback Customer",
    "summary": """
        Group Customer""",
    "description": """
        Group Customer
    """,
    "author": "ALPHASOFT",
    "website": "www.alphasoft.id",
    "category": "account",
    "version": "15.0.0",

    'depends': ['base','sale','mail','account','stock','aos_product_adireksa'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cashback_invoice_sequence.xml',
        'views/menu_item.xml',
        'views/cashback_rule.xml',
        'views/cashback_invoice.xml',
        'views/cashback_manual.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/cashback_product.xml',
        'views/cashback_internal_category.xml',
        'views/cashback_internal_category_class.xml',
        'views/account_payment_term.xml',
        'views/cashback_class_group.xml',
        'wizard/claim_cashback_wizard.xml',
        'wizard/cashback_manual_wizard.xml',
        'views/product_pricelist.xml',
        'views/customer_target.xml',
        'views/customer_cashback.xml',
        'views/res_partner.xml'
        ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    "auto_install": False,
    "application": True,
}
