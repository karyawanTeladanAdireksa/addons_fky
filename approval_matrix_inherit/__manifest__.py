# -*- coding: utf-8 -*-
{
    'name': 'Approval Matrix Inherit',
    'version': '15.0.0.0',
    'category': 'Approval Matrix',
    'sequence': 10,
    'summary': '',
    'description': '''
    Adding new field in approval.matrix.document.approval
    ''',
    'website': 'http://www.dev.com/',
    'author': 'dev/Alphasoft',
    'depends': ['base','approval_matrix'],

    'data': [
       'security/security.xml',  
       'views/approval_matrix_document_approval.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}