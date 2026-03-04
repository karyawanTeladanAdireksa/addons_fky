# -*- coding: utf-8 -*-
{
    "name": "Cashback Report",
    "author": "HashMicro/ Vadivel Duraisamy",
    "version": "10.1.0",
    "website": "www.hashmicro.com",
    "category": "Accounting",
    'summary': 'Cashback Report',
    'description': """
        Add field: 
        • Company ( Char | Many2one of res.company | Editable )
        • Customer ( Char | many2one of res.partner | Editable )
        • From Date ( Date | Editable )
        • To Date ( Date | Editable )
    
        Add Button:
            • PDF
            • XLS
            • Cancel
    
        Add trigger:
            • When user click menu Cashback Customer, it will pop up window wizard form view
            • When user click PDF button, it will generate and download report in PDF type
            • When user click XLS button, it will generate and download report in Excels type
            • When user click Cancel button, it will close the wizard

    """,
    "depends": ['account', 'aos_cashback'],
    "data": [
        'security/ir.model.access.csv',
        'report/report_actions.xml',
        'report/cashback_report_template.xml',
        'wizard/cashback_print_wizard.xml', 
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}