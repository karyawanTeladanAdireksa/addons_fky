{
    'name': 'Sale Request Modifier',
    'summary': 'Adireksa Sales Request Modifier',
    'depends': [
        'sales_team', 'account', 'stock', 'base','sale'
    ],
    'description': " ",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/ Balaji - (AntsyZ)',
    'data': [
        'data/ir_sequence_data.xml',
        'views/sale_request_views.xml',
        # 'views/sale_order_modify_views.xml',
        # 'wizard/sale_request_warning_message_view.xml',
    ],

    'installable': True,
    'auto_install': False,
}