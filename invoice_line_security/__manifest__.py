# -*- coding: utf-8 -*-
{
	'name' : 'Access Right To Update Invoice Line',
	'version' : '15.0.0.1',
	'category': 'Tools',
	'author': 'Syabani',
	'description': """
                Separate Customer Per Group to edit quantity, discount, price unit
        """,
	'website': '',
	'depends' : ['base','account'],
	'data': [
		'security/res_groups.xml',
        'views/account_move_view.xml',
	],
	'demo': [
	],
	'installable': True,
	'application': False,
	'auto_install': False,
}
