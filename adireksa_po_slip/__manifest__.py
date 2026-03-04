# -*- coding: utf-8 -*-
{
    'name': 'Adireksa - Creating PO Slip',
    'version': '1.0',
    'category': 'Purchase',
    'sequence': 10,
    'summary': 'Create print out slip for PO',
    'description': '''
               a. Create layout as template below: 
               b. Get the value with following details:
                    Header Section:
                        • Header  Please show the company name and address base on user branch login
                        • Invoice  Label hardcode it and change to Purchase Order
                        • Invoice No. :  please change the label to Purchase Order No. then get the value from purchase order auto generated sequence number
                        • Messrs  Please change the label to “Supplier”. Get the name from selected res.partner in purchase.order
                        • Date  get from Order Date field from purchase.order
                        • Term of Payment  get from property_supplier_payment_term_id in res.partner
                        
                    Treeview section:
                        • MOTORCYCLE PARTS  label hardcode it
                        • Seq  sequence number in each line
                        • Item No.  get from Internal References from selected product in product.product
                        • Description  get from Name field from selected product in product.product
                        • Quantity  get from Quantity column from selected product in purchase.order
                        • Unit Price  get from Unit Price column from selected product in purchase.order
                        • Amount (US$)  get from Discounted Subtotal column from selected product in purchase.order
                        • Keterangan  get from Keterangan column in purchase.order
                        • Total Amount  Please put it below or at the end of the last product. Get from amount_total field from purchase.order
                        
               c. Add print button in purchase.order named Print PO Slip on the right menu
                  N.B: please also add this print button in menu Purchase Supplier (adireksa_purchase_supplier) and Purchase Vendor (adireksa_purchase_vendor)
                
    ''',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/ Vadivel Duraisamy',
    'depends': ['purchase'],
    'data': [
             'reports/report_actions.xml',
             'reports/report_po_slip_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}