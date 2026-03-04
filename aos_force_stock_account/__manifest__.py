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
    'name': 'Stock Force Account',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'author': "Alphasoft",
    'sequence': 1,
    'website': 'https://www.alphasoft.co.id/',
    'images' : ['images/main_screenshot.png'],
    'category': 'Accounting',
    'summary': 'Stock Force Account',
    'depends': ['stock_account',],
    'description': """
Force Account and Force Date Accounting
=====================================================
* Stock Adjustment
* Stock Picking
* Allowed to Backdate on inventory adjustment and date transfer
""",
    'demo': [],
    'test': [],
    'data': [
        "security/stock_security.xml",
        'views/res_partner_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_picking_type_view.xml',
     ],
    'css': [],
    'js': [],
    'price': 0.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
