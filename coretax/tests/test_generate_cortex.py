from lxml import etree
from odoo.tests import tagged, common

@tagged('post_install', '-at_install')
class TestCortexLXML(common.TransactionCase):
    def setUp(self):
        """
        """
        super().setUp()

        self.maxDiff = 1500
        # change company info for csv detai later
        self.env.company.country_id = self.env.ref('base.id')
        self.env.company.account_fiscal_country_id = self.env.company.country_id
        self.env.company.street = "test"
        self.env.company.phone = "12345"

        self.partner_id = self.env['res.partner'].create({"name": "cortex_test", "vat": "000000000000000"})
        self.env['account.tax.group'].create({
            'name': 'tax_group',
            'country_id': self.env.ref('base.id').id,
        })
        self.partner_id_vat = self.env['res.partner'].create({"name": "cortex_test2", "vat": "010000000000000"})
        self.tax_id = self.env['account.tax'].create({"name": "test tax", "type_tax_use": "sale", "amount": 10.0, "price_include": True})

        self.out_invoice_1 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': '2019-05-01',
            'date': '2019-05-01',
            'invoice_line_ids': [
                (0, 0, {'name': 'line1', 'price_unit': 110.0, 'tax_ids': self.tax_id.ids}),
            ],
        })
        self.out_invoice_1.action_post()

        self.out_invoice_2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': '2019-05-01',
            'date': '2019-05-01',
            'invoice_line_ids': [
                (0, 0, {'name': 'line1', 'price_unit': 110.11, 'quantity': 400, 'tax_ids': self.tax_id.ids})
            ],
        })
        self.out_invoice_2.action_post()
        