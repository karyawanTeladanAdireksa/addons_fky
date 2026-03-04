# -*- coding: utf-8 -*-

from odoo import models, fields, api

from functools import lru_cache


class AccountVoucherReport(models.Model):
    _name = "account.voucher.report"
    _description = "Voucher Statistics"
    _auto = False
    _rec_name = 'voucher_date'
    _order = 'voucher_date desc'

    # ==== Voucher fields ====
    number = fields.Char('Number', readonly=True)
    payment_memo = fields.Char('Payment Memo', readonly=True)
    number_invoice = fields.Char('Invoice', readonly=True)
    number_cheque = fields.Char('Cheque', readonly=True)
    move_id = fields.Many2one('account.move', readonly=True)
    payment_journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', string='Partner Company', help="Commercial Entity")
    country_id = fields.Many2one('res.country', string="Country")
    voucher_user_id = fields.Many2one('res.users', string='Responsible', readonly=True)
    # move_type = fields.Selection([
    #     ('out_invoice', 'Customer Invoice'),
    #     ('in_invoice', 'Vendor Bill'),
    #     ('out_refund', 'Customer Credit Note'),
    #     ('in_refund', 'Vendor Credit Note'),
    #     ], readonly=True)
    voucher_type = fields.Selection([
        ('sale', 'Receipt'),
        ('purchase', 'Payment')
        ], string='Type', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirm'),
        #('waiting_approval','Waiting Approval'),
        #('approved', 'Approved'),
        ('in_payment', 'In Payment'),
        ('posted', 'Posted'),
        ], string='Voucher Status', readonly=True)
    # payment_state = fields.Selection(selection=[
    #     ('not_paid', 'Not Paid'),
    #     ('in_payment', 'In Payment'),
    #     ('paid', 'paid')
    # ], string='Payment Status', readonly=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', readonly=True)
    voucher_date = fields.Date(readonly=True, string="Invoice Date")

    # ==== Invoice line fields ====
    product_name = fields.Char('Description')
    quantity = fields.Float(string='Product Quantity', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    account_date = fields.Date(string='Accounting Date', readonly=True)
    account_id = fields.Many2one('account.account', string='Revenue/Expense Account', readonly=True, domain=[('deprecated', '=', False)])
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', groups="analytic.group_analytic_accounting")
    price_subtotal = fields.Float(string='Untaxed Total', readonly=True)
    price_average = fields.Float(string='Average Price', readonly=True, group_operator="avg")

    _depends = {
        'account.voucher': [
            'number', 'name', 'number_invoice', 'number_cheque', 'state', 'voucher_type', 'partner_id', 'user_id', 'fiscal_position_id',
            'date', 'account_date', 'payment_journal_id',
        ],
        'account.voucher.line': [
            'name', 'quantity', 'price_subtotal', 
            'voucher_id', 'product_id', 'uom_id', 'account_id', 'account_analytic_id',
            'company_id', 'currency_id',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
        'uom.uom': ['category_id', 'factor', 'name', 'uom_type'],
        'res.currency.rate': ['currency_id', 'name'],
        'res.partner': ['country_id'],
    }

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return '''
            SELECT
                line.id,
                voucher.move_id,
                voucher.number,
                voucher.number_invoice,
                voucher.number_cheque,
                voucher.name as payment_memo,
                line.name as product_name,
                line.product_id,
                line.account_id,
                line.account_analytic_id,
                voucher.payment_journal_id,
                line.company_id,
                line.company_currency_id,
                voucher.partner_id AS commercial_partner_id,
                voucher.state,
                voucher.voucher_type,
                line.partner_id,
                voucher.user_id AS voucher_user_id,
                voucher.fiscal_position_id,
                voucher.date AS voucher_date,
                voucher.account_date,
                uom_template.id AS uom_id,
                template.categ_id AS product_categ_id,
                line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (CASE WHEN voucher.voucher_type = 'purchase' THEN -1 ELSE 1 END)
                AS quantity,
                line.price_subtotal * currency_table.rate AS price_subtotal,
                -COALESCE(
                   -- Average line price
                   (line.price_subtotal / NULLIF(line.quantity, 0.0)) * (CASE WHEN voucher.voucher_type IN ('purchase') THEN -1 ELSE 1 END)
                   -- convert to template uom
                   * (NULLIF(COALESCE(uom_line.factor, 1), 0.0) / NULLIF(COALESCE(uom_template.factor, 1), 0.0)),
                   0.0) * currency_table.rate AS price_average,
                COALESCE(partner.country_id, commercial_partner.country_id) AS country_id
        '''

    @api.model
    def _from(self):
        return '''
            FROM account_voucher_line line
                INNER JOIN account_voucher voucher ON voucher.id = line.voucher_id
                LEFT JOIN res_partner partner ON partner.id = voucher.partner_id
                LEFT JOIN product_product product ON product.id = line.product_id
                LEFT JOIN account_account account ON account.id = line.account_id
                LEFT JOIN account_account_type user_type ON user_type.id = account.user_type_id
                LEFT JOIN product_template template ON template.id = product.product_tmpl_id
                LEFT JOIN uom_uom uom_line ON uom_line.id = line.uom_id
                LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                LEFT JOIN res_partner commercial_partner ON commercial_partner.id = voucher.partner_id
                JOIN {currency_table} ON currency_table.company_id = line.company_id
        '''.format(
            currency_table=self.env['res.currency']._get_query_currency_table({'multi_company': True, 'date': {'date_to': fields.Date.today()}}),
        )

    @api.model
    def _where(self):
        return '''
            WHERE voucher.voucher_type IN ('sale', 'purchase')
                AND line.account_id IS NOT NULL
        '''


# class ReportVoucherWithoutPayment(models.AbstractModel):
#     _name = 'report.aos_account_voucher.report_voucher'
#     _description = 'Account report without payment lines'

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         docs = self.env['account.voucher'].browse(docids)

#         # qr_code_urls = {}
#         # for voucher in docs:
#         #     if voucher.display_qr_code:
#         #         new_code_url = voucher.generate_qr_code()
#         #         if new_code_url:
#         #             qr_code_urls[voucher.id] = new_code_url

#         return {
#             'doc_ids': docids,
#             'doc_model': 'account.voucher',
#             'docs': docs,
#             # 'qr_code_urls': qr_code_urls,
#         }