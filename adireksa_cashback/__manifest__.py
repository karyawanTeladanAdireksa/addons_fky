# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Cashback',
    'version': '15.0.0',
    'category': 'Accounting',
    'sequence': 12,
    'summary': 'Adding cashback feature in customer invoice based on Customer Omset and Cashback Master',
    'description': ''' Create new object & module for cashback
                       Add field: 
                            • Cashback Name (Char | Required | Editable)
                            • Kelas Customer (Char | Selection: 
                            • Blue (Annapurna)
                            • Platinum
                            • Gold
                            • Silver
                            • Kelas 2 & Kelas 1 | Editable)
                            • Jenis Omset (Char | Selection:
                            • Bulanan
                            • Quarter
                            • Annual | Editable | Required)
                            • Jenis Cashback ( Char | Selection:
                            • Bulanan
                            • Quarterly
                            • Annual
                            • Pelunasan
                            • Promo | Editable | Required)
                        
                            • Periode Start Date (date | autofill with current sys date | editable )
                            • Periode End Date (date | autofill with current sys date | editable )
                            • Aktifkan Cashback (Boolean)
                        
                        Add in tree view:
                        Cashback Formula (Int | Required | Editable)
                        
                        
                        Add Button:
                            • Edit
                            • Save
                            • Request for Approval
                            • Approved
                            • Reset
                        
                        Add State:
                            • Draft
                            • Request for Approval
                            • Approved
                        
                        
                        Add trigger:
                            • When user click Save button, the state will become “Draft”
                            • When user click Request for Approval button, the state will be change from “Draft” to “Request for Approval”
                            • When user click Approved button, the state will be change from “Request for Approval” to “Approved”
                            • When user click Reset button, the state will be change to Draft again
                            
                    
 ''',
    'website': 'https://www.alphasoft.co.id/',
    'author': 'Alphasoft',
    'depends': ['adireksa_kelas_customer','sale'],
    'data': [
        'security/ir.model.access.csv',
        # 'wizard/sale_make_invoice_advance.xml',
        'views/cashback_view.xml',
        'views/account_invoice.xml',
        'views/sale.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}