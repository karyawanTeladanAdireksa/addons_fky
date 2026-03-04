# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2017 Alphasoft
#    (<http://www.alphasoft.co.id>).
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
    'name': 'Approval Matrix',
    'version': '15.0.0.1.0',
    'license': 'OPL-1',
    'author': "Alphasoft",
    'sequence': 1,
    'website': 'https://www.alphasoft.co.id/',
    'images':  ['images/main_screenshot.png'],
    'category': 'Sales',
    'summary': 'Approval Matrix for any model',
    'depends': ['base', 'web_many2one_reference', 'hr', 'generic_m2o'],
    'description': """Approval Matrix for any model. You just only need call approval_matrix_validation() on Alphasoft""",
    'demo': [],
    'test': [],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/mail_data.xml',
        'views/approval_matrix.xml',
        'views/approval_matrix_document_approval.xml',
        'views/rejection_message.xml',
        'views/message_post_wizard.xml',
        
    ],
    'css': [],
    'js': [],
    'price': 10.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}