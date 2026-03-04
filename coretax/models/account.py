import math
import base64
import io
from datetime import datetime, date
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, _, api
from odoo.tools import float_repr
from odoo.tools.misc import xlsxwriter
import logging

_logger = logging.getLogger(__name__)

DECIMAL_DIGITS = 2
TAXES_DIGITS = 2
PPN_11 = 11.0
PPN_12 = 12.0
XLSX_FLOAT_FORMAT = '#,##0.00'
XLSX_MONETARY_FORMAT = "#,##0.00"

def date_parse(value):
    if not isinstance(value, (datetime, date)):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value.strftime("%Y-%m-%d")
    
def float_repr_round_down(value, decimal_digits):
    """
    Rounds down a floating-point value to a specified number of decimal digits 
    and converts it to a string using Odoo's float_repr.

    :param value: The float value to round down.
    :param decimal_digits: The number of decimal digits to retain.
    :return: The rounded down value as a string.
    """
    factor = 10 ** decimal_digits
    rounded_value = math.floor(value * factor) / factor
    return float_repr(rounded_value, decimal_digits)
    
def set_sub_element(parent_element, element_name, value=None, **attributes):
    """helper function to set SubElement and value
    
    :param parent_element: parent node
    :param element_name: sub element yang akan diappend ke parent element
    :param value: value yang akan di set ke sub element yang dibuat
    """
    el = etree.SubElement(parent_element, element_name, **attributes)
    if value:
        el.text = value if not isinstance(value, float) else float_repr(value, DECIMAL_DIGITS)
    return el

class AccountMove(models.Model):
    _inherit = "account.move"

    coretax_need_kode_transaksi = fields.Boolean(compute='_compute_coretax_need_kode_transaksi')
    coretax_download_xml = fields.Boolean(default=False)
    coretax_download_xlsx = fields.Boolean(default=False)

    #OVERIDE SINCE WE NOT USING EFAKTUR IN 2025
    @api.onchange('l10n_id_tax_number')
    def _onchange_l10n_id_tax_number(self):
        for record in self:
            if record.l10n_id_tax_number and record.move_type not in self.get_purchase_types():
                _logger.info("By Pass this Error")
                #raise UserError(_("You can only change the number manually for a Vendor Bills and Credit Notes"))

    #OVERIDE SINCE WE NOT USING EFAKTUR IN 2025
    @api.depends('partner_id')
    def _compute_need_kode_transaksi(self):
        for move in self:
            # If there are no taxes at all on every line (0% taxes counts as having a tax) then we don't need a kode transaksi
            # move.l10n_id_need_kode_transaksi = (
            #     move.partner_id.l10n_id_pkp
            #     and not move.l10n_id_tax_number
            #     and move.move_type == 'out_invoice'
            #     and move.country_code == 'ID'
            #     and move.line_ids.tax_ids
            # )
            move.l10n_id_need_kode_transaksi = move.partner_id.l10n_id_need_kode_transaksi

    @api.depends('partner_id', 'partner_id.l10n_id_kode_transaksi', 'line_ids.tax_ids')
    def _compute_coretax_need_kode_transaksi(self):
        for move in self:
            # If there are no taxes at all on every line (0% taxes counts as having a tax) then we don't need a kode transaksi
            move.coretax_need_kode_transaksi = (
                move.partner_id.l10n_id_pkp
                # and not move.l10n_id_tax_number
                and move.move_type == 'out_invoice'
                and move.country_code == 'ID'
                and move.line_ids.tax_ids
            )

    def _get_document_number(self):
        document = ''
        if self.partner_id.coretax_type == 'TIN':#NPWP
            document = '-'
        elif self.partner_id.coretax_type == 'National ID':#KTP
            if not self.partner_id.l10n_id_nik:
                raise UserError(_('Coretax National ID should define first %s' % self.partner_id.name))
            document = self.partner_id.l10n_id_nik
        elif self.partner_id.coretax_type == 'Passport':#Passport
            if not self.partner_id.l10n_id_passport:
                raise UserError(_('Coretax Passport should define first %s' % self.partner_id.name))
            document = self.partner_id.l10n_id_passport
        elif self.partner_id.coretax_type == 'Other ID':#Other ID
            if not self.partner_id.l10n_id_other:
                raise UserError(_('Coretax Other ID should define first %s' % self.partner_id.name))
            document = self.partner_id.l10n_id_other
        return document

    def set_invoice_line_tag(self, invoices_lines):
        tax_calculation_coretax = self.company_id.tax_calculation_coretax
        InvoiceLineRoot = etree.Element("ListOfGoodService")
        discount_coupon = abs(sum(self.invoice_line_ids.filtered(lambda l: 'Discount:' in l.name and l.price_unit < 0.0).mapped('price_subtotal')))#PASTI MINUS
        total_units = abs(sum(self.invoice_line_ids.filtered(lambda l: 'Discount:' not in l.name and l.price_unit > 0.0).mapped('price_subtotal')))#TOTAL BUKAN DISKON
        # discount_ppn_coupon = abs(sum(self.invoice_line_ids.filtered(lambda l: 'Discount:' in l.name and l.price_unit < 0.0).mapped('price_tax')))
        # total_ppn_units = abs(sum(self.invoice_line_ids.filtered(lambda l: 'Discount:' not in l.name and l.price_unit > 0.0).mapped('price_tax')))#TOTAL BUKAN DISKON
        #DISKON GA JADI BARIS
        for line in invoices_lines.filtered(lambda l: not l.exclude_from_invoice_tab and 'Discount:' not in l.name):
            InvoiceLine = set_sub_element(InvoiceLineRoot, "GoodService", None)
            coretax_product = line.product_id.coretax_product_id
            coretax_uom = line.product_uom_id.coretax_uom_id
            #LOGIC v1
            # line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            # taxBase = (line.price_unit * line.quantity) - line_discount_price_unit
            # otherTaxBase = ((line.price_unit * line.quantity) - line_discount_price_unit) * (PPN_11/PPN_12)
            discount_coupon_unit = round((line.price_total / (total_units or 1)) * discount_coupon, 2)
            # discount_coupon_ppn_unit = round((line.price_tax / (total_ppn_units or 1)) * discount_ppn_coupon, 2)
            #===============================================================
            # line_dpp = line.price_subtotal - discount_coupon_unit#int(round(self._amount_currency_line(line.price_subtotal - discount_coupon_unit, line), 0))
            # line_ppn = line.tax_ids and line.price_tax - discount_coupon_ppn_unit#int(round(self._amount_currency_line(line.price_tax - discount_coupon_ppn_unit, line),0))
            #LOGIC v2
            line_discount_price_unit = 0.0#(line.price_unit) - (line.price_unit * (1 - (line.discount / 100.0)))
            # line_after_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            line_after_discount_coupon_price_unit = (line.price_total - discount_coupon_unit) / line.quantity if line.quantity else 1.0
            # line.price_subtotal - discount_coupon_unit
            taxBase = 0.0
            otherTaxBase = 0.0
            vat = 0.0
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_after_discount_coupon_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.belongs_to_refund(),
                )
                taxBase = taxes_res['taxes'][0]['base']
                otherTaxBase = taxBase * (eval(tax_calculation_coretax) if self.l10n_id_kode_transaksi == '04' else 1)
                vat = float_repr_round_down(otherTaxBase * (int(tax_calculation_coretax.split('/')[1] if '/' in tax_calculation_coretax else 12.0)/100.0), DECIMAL_DIGITS)#taxes_res['taxes'][0]['amount']
            if not coretax_product:
                raise UserError(_('Coretax Product Code should define first %s' % line.product_id.name))
            if not coretax_uom:
                raise UserError(_('Coretax UoM Code should define first %s' % line.product_id.name))
            set_sub_element(InvoiceLine, "Opt", 'B' if line.product_id.detailed_type == 'service' else 'A')
            set_sub_element(InvoiceLine, "Code", coretax_product.code)
            set_sub_element(InvoiceLine, "Name", line.product_id.name + (' ' + line.product_id.product_brand.name) if line.product_id.product_brand else '' or line.product_id.name)#TAMBAH BRAND UTK ADIREKSA
            set_sub_element(InvoiceLine, "Unit", coretax_uom.code)
            set_sub_element(InvoiceLine, "Price", (taxBase / (line.quantity or 1.0)) or 0)
            set_sub_element(InvoiceLine, "Qty", line.quantity)
            set_sub_element(InvoiceLine, "TotalDiscount", line_discount_price_unit or '0')
            set_sub_element(InvoiceLine, "TaxBase", taxBase)
            set_sub_element(InvoiceLine, "OtherTaxBase", otherTaxBase if self.l10n_id_kode_transaksi == '04' else taxBase) # TODO: Jika tidak menggunakan Other Taxbase diisi dengan jumlah yang sama dengan TaxBase. Jika menggunakan Other Taxbase maks value sama dengan TaxBase
            set_sub_element(InvoiceLine, "VATRate", str(tax_calculation_coretax.split('/')[1]))
            set_sub_element(InvoiceLine, "VAT", vat)
            set_sub_element(InvoiceLine, "STLGRate", "0") # TODO: set STLG rate
            set_sub_element(InvoiceLine, "STLG", "0") # TODO: set STLG
        return InvoiceLineRoot

    def set_invoice_tag(self):
        """Set element tag for invoice
        """
        self.ensure_one()
        if not self.company_id.partner_id.vat and len(self.company_id.partner_id.vat) != 16:
            raise UserError(_('NPWP Company is required'))
        if not self.partner_id.coretax_type:
            raise UserError(_('Customer Coretax ID Type required'))
        InvoiceRoot = etree.Element("TaxInvoice")
        set_sub_element(InvoiceRoot, "TaxInvoiceDate", date_parse(self.invoice_date))
        set_sub_element(InvoiceRoot, "TaxInvoiceOpt", "Normal") # static value
        set_sub_element(InvoiceRoot, "TrxCode", self.l10n_id_kode_transaksi)
        set_sub_element(InvoiceRoot, "AddInfo", None) # TODO: set add info
        set_sub_element(InvoiceRoot, 'CustomDoc', None) # TODO: set custom doc
        set_sub_element(InvoiceRoot, 'RefDesc', self.name or self.ref)
        set_sub_element(InvoiceRoot, "FacilityStamp", None) # TODO: set facility stamp
        set_sub_element(InvoiceRoot, "SellerIDTKU", str(self.company_id.partner_id.vat or '') + '000000') # TODO: concat sisa 6 digit ID TKU (vat(done) + ID TKU)
        set_sub_element(InvoiceRoot, "BuyerTin", self.partner_id.vat.replace('-','').replace('.','') if self.partner_id.vat and self.partner_id.coretax_type == 'TIN' else '0000000000000000')
        set_sub_element(InvoiceRoot, "BuyerDocument", self.partner_id.coretax_type)
        set_sub_element(InvoiceRoot, "BuyerCountry", self.partner_id.country_id.coretax_code or 'IDN')
        set_sub_element(InvoiceRoot, "BuyerDocumentNumber", self._get_document_number())
        set_sub_element(InvoiceRoot, "BuyerName", self.partner_id.l10n_id_tax_name or self.partner_id.name)
        set_sub_element(InvoiceRoot, "BuyerAdress", self.partner_id.l10n_id_tax_address or self.partner_id._display_coretax_address(without_company=True))
        set_sub_element(InvoiceRoot, "BuyerEmail", self.partner_id.email)
        set_sub_element(InvoiceRoot, "BuyerIDTKU", str(self.partner_id.vat.replace('-','').replace('.','') if self.partner_id.vat and self.partner_id.coretax_type == 'TIN' else '') + '000000') # TODO: concat sisa 6 digit ID TKU (vat(done) + ID TKU)
        InvoiceLineEl = self.set_invoice_line_tag(self.invoice_line_ids)
        InvoiceRoot.append(InvoiceLineEl)
        return InvoiceRoot
    
    def generate_coretax_report(self):
        root = etree.Element("TaxInvoiceBulk")
        companies = self.company_id
        for company in companies:
            set_sub_element(root, "TIN", company.partner_id.vat)
            invoice_root = etree.Element("ListOfTaxInvoice")
            for invoice in self.filtered(lambda r: r.company_id.id == company.id):
                invoiceList = invoice.set_invoice_tag()
                invoice_root.append(invoiceList)
            # root.append(company_root)
            root.append(invoice_root)
        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        # single_invoice = self.name.replace('/','_').replace(' ','_').replace('.','_')
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(xml),
            'name': 'Coretax_%s.xml' % fields.Datetime.to_string(fields.Datetime.now()).replace(" ", "_"),
            'type': 'binary',
        })

        for record in self:
            record.coretax_download_xml = True
            record.message_post(attachment_ids=[attachment.id])
        return attachment 
        
    def download_coretax_lxml(self):
        attachment = self.generate_coretax_report()
        return self.download_coretax(attachment)
    
    # following style base export
    def _get_faktur_header(self):
        return ["Baris", "Tanggal Faktur", "Jenis Faktur", "Kode Transaksi", 
                "Keterangan Tambahan", "Dokumen Pendukung", "Referensi", 
                "Cap Fasilitas", "ID TKU Penjual", "NPWP/NIK Pembeli", 
                "Jenis ID Pembeli", "Negara Pembeli", "Nomer Dokumen Pembeli", 
                "Nama Pembeli", "Alamat Pembeli", "Email Pembeli", "ID TKU Pembeli"]
    
    def _get_detail_header(self):
        return ["Baris", "Barang/Jasa", "Kode Barang Jasa", "Nama Barang/Jasa",
                "Nama Satuan Ukur", "Harga Satuan", "Jumlah Barang Jasa", 
                "Total Diskon", "DPP", "DPP Nilai Lain", "Tarif PPN",
                "PPN", "Tarif PPnBM", "PPnBM"]
    
    def _get_faktur_data(self, baris):
        def display_name_selection(fields_obj, value):
            """Get display name / label dari selection"""
            for selection in fields_obj._description_selection(self.env):
                if selection[0] == value:
                    return selection[1]
            return value
        # date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        # ordering by header
        tax_calculation_coretax = self.company_id.tax_calculation_coretax
        discount_coupon = abs(sum(self.invoice_line_ids.filtered(lambda l: 'Discount:' in l.name and l.price_unit < 0.0).mapped('price_subtotal')))#PASTI MINUS
        total_units = abs(sum(self.invoice_line_ids.filtered(lambda l: 'Discount:' not in l.name and l.price_unit > 0.0).mapped('price_subtotal')))#TOTAL BUKAN DISKON
        # print ('==self.invoice_date==',self.invoice_date)
        faktur_data = [
            str(int(baris)),
            self.invoice_date,
            "Normal", # static value
            self.l10n_id_kode_transaksi,
            "", # TODO: Keterangan Tambahan
            "", # TODO: Dokumen Pendukung
            self.name or self.ref,
            "", # TODO: Cap Fasilitas
            str(self.company_id.partner_id.vat or '') + '000000',
            self.partner_id.vat.replace('-','').replace('.','') if self.partner_id.vat and self.partner_id.coretax_type == 'TIN' else '0000000000000000',
            display_name_selection(self.partner_id._fields['coretax_type'], self.partner_id.coretax_type),
            self.partner_id.country_id.coretax_code or 'IDN',
            self._get_document_number(),
            self.partner_id.l10n_id_tax_name or self.partner_id.name,
            self.partner_id.l10n_id_tax_address or self.partner_id._display_coretax_address(),
            self.partner_id.email,
            str(self.partner_id.vat.replace('-','').replace('.','') if self.partner_id.vat and self.partner_id.coretax_type == 'TIN' else '') + '000000'
        ]
        detail_data = []
        for line in self.invoice_line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and 'Discount:' not in l.name):
            discount_coupon_unit = round((line.price_total / (total_units or 1)) * discount_coupon, 2)
            # Ordering by header
            line_discount_price_unit = 0.0#(line.price_unit) - (line.price_unit * (1 - (line.discount / 100.0)))
            # line_after_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            line_after_discount_coupon_price_unit = (line.price_total - discount_coupon_unit) / line.quantity if line.quantity else 1.0
            taxBase = 0.0
            otherTaxBase = 0.0
            vat = 0.0
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_after_discount_coupon_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.belongs_to_refund(),
                ) 
                taxBase = taxes_res['taxes'][0]['base']
                otherTaxBase = taxBase * (eval(tax_calculation_coretax) if self.l10n_id_kode_transaksi == '04' else 1)
                vat = otherTaxBase * (int(tax_calculation_coretax.split('/')[1] if '/' in tax_calculation_coretax else 12.0)/100.0)#taxes_res['taxes'][0]['amount']
            # dpp = line.price_unit * (1-(line.discount or 0.0)/100.0)
            detail_data.append([
                str(int(baris)),
                ('B' if line.product_id.detailed_type == 'service' else 'A'),
                line.product_id.coretax_product_id.code,
                line.name,
                line.product_uom_id.coretax_uom_id.code,
                (taxBase / (line.quantity or 1.0)) or 0,
                line.quantity or 1,
                line_discount_price_unit or 0, # TODO: Total Diskon
                taxBase, #DPP NORRMAL
                otherTaxBase,#DPP NILAI LAIN
                str(tax_calculation_coretax.split('/')[1]), #TARIF PPN
                vat, #PPN
                float(0), # TODO: Tarif PPnBM
                float(0), # TODO: PPnBM
            ])
        # print ('==detail_data==',detail_data)
        return faktur_data, detail_data
        
    
    def generate_coretax_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        FakturSheet = workbook.add_worksheet("Faktur")
        DetailSheet = workbook.add_worksheet("DetailFaktur")
        header_style = workbook.add_format({'bold': True})
        base_style = workbook.add_format({'text_wrap': True})
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd/mm/yyyy'})
        datetime_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd/mm/yyyy hh:mm:ss'})
        
        def write_header(sheet, values=[], row=0):
            for i, value in enumerate(values):
                sheet.write(row, i, value, header_style)
            sheet.set_column(0, max(0, len(values) - 1), 30) # around 220 pixels
        
        def write_cell(sheet, row, column, cell_value):
            cell_style = base_style
            if cell_value in (None, False):
                cell_value = "" # empty cell
            if isinstance(cell_value, date):
                cell_style = date_style
            elif isinstance(cell_value, datetime):
                cell_style = datetime_style
            elif isinstance(cell_value, float):
                cell_style.set_num_format(XLSX_FLOAT_FORMAT)
            sheet.write(row, column, cell_value, cell_style)
        
        faktur_row = detail_row = 1
        for company in self.mapped('company_id'):
            if not company.partner_id.vat and len(company.partner_id.vat) != 16:
                raise UserError(_('NPWP Company is required %s' % company.name))
            write_header(FakturSheet, ['NPWP Penjual', '', company.vat], 0)
            write_header(FakturSheet, self._get_faktur_header(), faktur_row + 2 - 1)
            write_header(DetailSheet, self._get_detail_header(), detail_row - 1)
            moves = self.filtered(lambda r: r.company_id.id == company.id)
            line_counter = 1
            for move in moves:
                faktur_data, detail_data = move._get_faktur_data(line_counter)
                for i, data in enumerate(faktur_data):
                    write_cell(FakturSheet, faktur_row + 3 - 1, i, data)
                faktur_row += 1
                for line_row in detail_data:
                    for i, line_data in enumerate(line_row):
                        write_cell(DetailSheet, detail_row, i, line_data)
                    detail_row += 1
                write_cell(DetailSheet, detail_row, 0, 'END')#END OF DETAIL
                line_counter += 1
            write_cell(FakturSheet, line_counter+2, 0, "END")#END OF FAKTUR
        workbook.close()
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'datas': base64.encodebytes(output.read()),
            'name': 'Coretax_%s.xlsx' % fields.Datetime.to_string(fields.Datetime.now()).replace(" ", "_"),
            'type': 'binary',
        })

        for record in self:
            record.coretax_download_xlsx = True
            record.message_post(attachment_ids=[attachment.id])
        return attachment
    
    def download_coretax_xlsx(self):
        attachment = self.generate_coretax_xlsx()
        return self.download_coretax(attachment)
    
    def download_coretax(self, attachment):
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=ir.attachment&id=" + str(attachment.id) + "&filename_field=name&field=datas&download=true&name=" + attachment.name,
            'target': 'self'
        }
    