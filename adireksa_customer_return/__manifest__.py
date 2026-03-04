# -*- coding: utf-8 -*-
{
    'name': "Adireksa - Report Sales Return",
    'summary': """Customer Return module""",
    'description': """
        Customer Return, entry like Invoice, needs approval level, reduce A/R, auto generate journal.
    """,
    'author': 'Alphasoft',
    'category': 'Sale',
    'sequence': 16,
    'version': '15.0.0.1',
    'depends': ['aos_sales_return'],
    'data': [
        # 'security/customer_return_security.xml',
        # 'security/ir.model.access.csv',
        # 'data/customer_return_data.xml',
        # 'views/customer_return_view.xml', 
        'report/report_action.xml',
        'report/report_penerimaan_barang_template.xml',
        'report/report_pengembalian_barang_template.xml', 
        'report/report_blanko_penerimaan.xml',
        # 'report/report_surat_barang_retur.xml',
        # 'report/report_customer_return.xml',
    ],
    'installable': True,
    'application': True,
}
