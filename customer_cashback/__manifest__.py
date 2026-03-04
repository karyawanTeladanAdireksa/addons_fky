# -*- coding: utf-8 -*-
{
    'name': 'Customer Cashback',
    'version': '1.5.5',
    'category': 'Accounting',
    'sequence': 10,
    'summary': 'Create new object & module for Customer Cashback',
    'description': '''
                Create a new menu item named “Customer Cashback” under Accounting.
            V 1.1
            	Add JE when confirm SO and Register Payment
            V 1.2
                - Setting Active Cashback SO Date
                - Add field Cashback Generate in Customer
                - Omset Master Customer
                    - Add onset fields in Customer
                - Master Type Cashback
                    - Add comapny, manual cashback, default posting fields
                - Master Customer Cashback 
                    - Add company, cashback pending fields
                    - Create Cashback Transaction Manual 
                - Master Cashback Product
                    - Add company, start date, end date fields
                - Cashback Customer Invoice
                    - Add cashback per, invoice age fields
                - Acces Right Cashback Customer
                    - Show Customer Menu Group
                    - Manger Group
            V 1.3
                - Need to add adireksa_kelas_customer module in depends
            V 1.4
                - ACCOUNTING > SETTING
                    1. Add “Cashback Deduction Option” Field in the Accounting > Setting > Cashback Customer Invoice, with selection : “Sales Order” and “Customer Invoice”
                    2. Rename “Cashback Customer Invoice” into “Cashback Setting”
                - CASHBACK TYPE
                    1. Rename the “Sale Order” into “Sale Order (In)
                    2. Create New data “Sale Order (Used)“, Default Posting = Credit; that cannot be deleted
                - MASTER CASHBACK CUSTOMER
                    1. Cashback Transaction Summary :  Add status in the field.
                    2. If “Cashback Deduction Option” = “Customer Invoice” then :
                        a. At “Cashback Transaction Manual > Create Cashback” when validate create JE like in SO
                    3. Cashback Pending =  Total value from “Cashback Transaction Summary” with status  = pending, related to task Sales Order point 2 ii
                    4. Field “Cashback Account” and “Cashback Expense Cashback” mandatory if “Cashback Deduction Option” = “Customer Invoice”
                - Other Changes in Sale Order And Invoice as per document (Cashback 3)
            V  1.5
                - Fixed Issue as per Doc(Cashback 4)
                - V 1.5.1
                    - Add new state(waiting for approval) in Cashback Manual
                - V 1.5.2
                    - Add company Filter for Master cashback customer and master cashback product
                - V 1.5.3
                    - Change code to show cashback field in customer invoice
                    - Add warning for cashback cannot bigger than max cashback
                - V 1.5.4
                    - Change the formula for cashback In (Debit and Approve)
                    - Change the formula for cashback Used (Credit and Approve)
                - V 1.5.5
                    - Change balance formula to not reduce the cashback pending value
                
    ''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/ Heer Patel / MissK',
    'depends': ['account','aos_cashback','sale'],
    'data': [
        'security/ir.model.access.csv',
        'security/cashback_security.xml',
        'data/ir_sequence_data.xml',
        # 'data/cashback_type_data.xml',
        # 'views/res_partner_view.xml',
        # 'views/account_payment_view.xml',
        # 'views/account_config_settings_view.xml',
        'wizard/create_manual_cashback_view.xml',
        'wizard/add_product_view.xml',
        'views/customer_cashback_views.xml',
        'views/cashback_type_views.xml',
        'views/cashback_product_views.xml',
        # 'views/sale_order_line_view.xml',
        # 'report/sale_request_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}