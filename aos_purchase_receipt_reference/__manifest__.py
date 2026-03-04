# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Receipt Vendor Reference",
    "author": "Syabani",
    "version": "15.0.0.1",
    "summary": "Add Vendor Reference On Receipt",
    "website": "",
    "depends": [
        "stock",
        "account",
        "purchase",
        "stock_picking_batch",
        "purchase_stock",
        "stock_account",
    ],
    "data": [
        'views/stock_picking_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_move_view.xml',
    ],
    "demo": [],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
