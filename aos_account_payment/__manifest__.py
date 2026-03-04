# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2017 Alphasoft
#    (<https://www.alphasoft.co.id/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Account Payment',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'author': "Alphasoft",
    'sequence': 1,
    'website': 'https://www.alphasoft.co.id/',
    'category': 'Accounting',
    'images':  ['images/main_screenshot.png'],
    'summary': 'Split Amount Payment',
    'depends': ['account'],
    'description': """
            Module based on Alphasoft
            ===================================================== 
            This module is aim to enhancement Account Payment
            * Split Amount Payment with multi invoice
     """,
    'demo': [],
    'test': [],
    'data': [
        "security/ir.model.access.csv",
        "wizard/account_register_payment_view.xml",
        'wizard/account_assign_invoice_views.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/res_config_settings_views.xml',
        #'views/menuitem_view.xml',
     ],
    'css': [],
    'js': [],
    'price': 483.97,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
