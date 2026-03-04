# -*- coding: utf-8 -*-
{
    'name': 'Odoo Customize Inherit',
    'version': '15.21.10.08',
    'author': 'Alphasoft',
    'category': 'Productivity',
    'sequence': 10,
    'description': 'Odoo Customize Inherit.',
    'summary': '',
    'website': 'http://web.antsyz.com/',
    'depends': ['app_odoo_customize',
                'aos_sales_return',
                'aos_sales_agreement',
                'aos_credit_limit_request',
                'aos_cashback',],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
}