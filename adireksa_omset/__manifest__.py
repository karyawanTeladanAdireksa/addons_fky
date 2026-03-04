# -*- coding: utf-8 -*-
{
    'name': 'Adireksa Omset - Create new object & module for cashback',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 10,
    'summary': 'Create new object & module for cashback',
    'description': '''
                Create a new menu item named “Omset Customer” under Accounting > Configuration.
    
                Add field: 
                • Omset Name (Char | Required | Editable)
                • Kelas Customer (Char | Selection: 
                • Blue (Annapurna)
                • Platinum
                • Gold
                • Silver
                • Kelas 2 & Kelas 1 | Editable | Required)
                • Jenis Omset (Char | Selection”
                • Bulanan
                • Quarter
                • Annual | Editable | Required)
                • Tahun (Int | Editable)
                • Periode Start Date (date | autofill with current sys date | editable )
                • Periode End Date (date | autofill with current sys date | editable )
                • Aktifkan Omset (Boolean)
            
            Add in tree view:
                • Nama Customer (Int | many2one of res.partner | Editable)
                • Target Omset (Int | Editable | Required)
                        
            Add Button:
                • Edit
                • Save
    
    ''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/ Vadivel Duraisamy',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/adireksa_omset.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}