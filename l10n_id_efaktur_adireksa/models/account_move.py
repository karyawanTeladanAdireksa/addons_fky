# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

FK_HEAD_LIST = ['FK', 'KD_JENIS_TRANSAKSI', 'FG_PENGGANTI', 'NOMOR_FAKTUR', 'MASA_PAJAK', 'TAHUN_PAJAK', 'TANGGAL_FAKTUR', 'NPWP', 'NAMA', 'ALAMAT_LENGKAP', 'JUMLAH_DPP', 'JUMLAH_PPN', 'JUMLAH_PPNBM', 'ID_KETERANGAN_TAMBAHAN', 'FG_UANG_MUKA', 'UANG_MUKA_DPP', 'UANG_MUKA_PPN', 'UANG_MUKA_PPNBM', 'REFERENSI', 'KODE_DOKUMEN_PENDUKUNG']

LT_HEAD_LIST = ['LT', 'NPWP', 'NAMA', 'JALAN', 'BLOK', 'NOMOR', 'RT', 'RW', 'KECAMATAN', 'KELURAHAN', 'KABUPATEN', 'PROPINSI', 'KODE_POS', 'NOMOR_TELEPON']

OF_HEAD_LIST = ['OF', 'KODE_OBJEK', 'NAMA', 'HARGA_SATUAN', 'JUMLAH_BARANG', 'HARGA_TOTAL', 'DISKON', 'DPP', 'PPN', 'TARIF_PPNBM', 'PPNBM']

def _csv_row(data, delimiter=',', quote='"'):
    return quote + (quote + delimiter + quote).join([str(x).replace(quote, '\\' + quote) for x in data]) + quote + '\n'


class AccountMove(models.Model):
    _inherit = "account.move"

    # l10n_id_need_kode_transaksi = fields.Boolean(compute='_compute_need_kode_transaksi')

    # @api.depends('partner_id')
    # def _compute_need_kode_transaksi(self):
    #     for move in self:
    #         move.l10n_id_need_kode_transaksi = move.partner_id.l10n_id_pkp and not move.l10n_id_tax_number and move.move_type == 'out_invoice' and move.country_code == 'ID'\
    #             and any(line.tax_ids for line in move.invoice_line_ids)

    def _amount_currency_line(self, amount, line):
        #amount = 0.0
        # print ('=awal=',amount)
        if line.tax_ids:
            cur_obj = self.env['res.currency']
            invoice_date = line.move_id.invoice_date or fields.Date.today()
            amount = line.move_id.currency_id._convert(amount, line.currency_id, line.company_id, invoice_date)
        # print ('=akhir=',amount)
        return amount

    def _generate_efaktur_invoice(self, delimiter):
        print ("""Generate E-Faktur for customer invoice adireksa.""")
        # Invoice of Customer
        company_id = self.company_id
        dp_product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')

        output_head = '%s%s%s' % (
            _csv_row(FK_HEAD_LIST, delimiter),
            _csv_row(LT_HEAD_LIST, delimiter),
            _csv_row(OF_HEAD_LIST, delimiter),
        )

        for move in self.filtered(lambda m: m.state == 'posted' and any(line.tax_ids for line in m.invoice_line_ids)):
            #CHECK APAKAH PRODUCT TERSBUT ADALAH DP
            #product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
            #product_downpayment = self.env['product.product'].browse(int(product_id)).exists()
            #print ('===product_downpayment===',product_downpayment)
            #===================================================================
            max_line_id = max(line for line in move.invoice_line_ids.filtered(lambda il: il.price_unit > 0) if line.tax_ids) or 0
            total_dpp = sum(int(round(self._amount_currency_line(line.price_subtotal, line),0)) for line in move.invoice_line_ids.filtered(lambda il: il.quantity > 0)) or 0
            total_ppn = sum(int(round(self._amount_currency_line(line.price_tax, line),0)) for line in move.invoice_line_ids.filtered(lambda il: il.quantity > 0)) or 0
            #print ('==max_line_id==',total_dpp,total_ppn)
            # tot_line_dpp = sum(int(round(self._amount_currency_line(line.price_subtotal, line),0)) for line in move.invoice_line_ids.filtered(lambda il: il.quantity > 0)) or 0
            # tot_line_ppn = sum(int(round(self._amount_currency_line(line.price_tax, line),0)) for line in move.invoice_line_ids.filtered(lambda il: il.quantity > 0)) or 0
            #===================================================================
            
            eTax = move._prepare_etax()

            nik = str(move.partner_id.l10n_id_nik) if not move.partner_id.vat else ''

            if move.l10n_id_replace_invoice_id:
                number_ref = str(move.l10n_id_replace_invoice_id.name) + " replaced by " + str(move.name) + " " + nik
            else:
                number_ref = str(move.name) + " " + nik

            street = ', '.join([x for x in (move.partner_id.street, move.partner_id.street2) if x])

            invoice_npwp = '000000000000000'
            if move.partner_id.vat and len(move.partner_id.vat) >= 12:
                invoice_npwp = move.partner_id.vat
            elif (not move.partner_id.vat or len(move.partner_id.vat) < 12) and move.partner_id.l10n_id_nik:
                invoice_npwp = move.partner_id.l10n_id_nik
            invoice_npwp = invoice_npwp.replace('.', '').replace('-', '')

            # Here all fields or columns based on eTax Invoice Third Party
            eTax['KD_JENIS_TRANSAKSI'] = move.l10n_id_tax_number[0:2] or 0
            eTax['FG_PENGGANTI'] = move.l10n_id_tax_number[2:3] or 0
            eTax['NOMOR_FAKTUR'] = move.l10n_id_tax_number[3:] or 0
            eTax['MASA_PAJAK'] = move.invoice_date.month
            eTax['TAHUN_PAJAK'] = move.invoice_date.year
            eTax['TANGGAL_FAKTUR'] = '{0}/{1}/{2}'.format(move.invoice_date.day, move.invoice_date.month, move.invoice_date.year)
            eTax['NPWP'] = invoice_npwp
            eTax['NAMA'] = move.partner_id.l10n_id_tax_name or move.partner_id.name# if eTax['NPWP'] == '000000000000000' else move.partner_id.l10n_id_tax_name or move.partner_id.name
            eTax['ALAMAT_LENGKAP'] = move.partner_id.contact_address.replace('\n', '') if eTax['NPWP'] == '000000000000000' else move.partner_id.l10n_id_tax_address or street
            #===================================================================
            amount_untaxed = total_dpp#int(round(total_dpp,0))
            amount_tax = total_ppn#int(round(total_ppn,0))
            # residual_dpp = amount_untaxed - tot_line_dpp
            # residual_ppn = amount_tax - tot_line_ppn
            # print ('---DPP--',amount_untaxed,tot_line_dpp)
            # print ('---PPN--',amount_tax,tot_line_ppn)
            # print ('---RESIDUAL--',residual_dpp,residual_ppn,residual_dpp+residual_ppn)
            #===================================================================
            eTax['JUMLAH_DPP'] = amount_untaxed#int(round(move.amount_untaxed, 0)) # currency rounded to the unit
            eTax['JUMLAH_PPN'] = amount_tax#int(round(move.amount_tax, 0))
            eTax['ID_KETERANGAN_TAMBAHAN'] = '1' if move.l10n_id_kode_transaksi == '07' else ''
            eTax['REFERENSI'] = number_ref
            eTax['KODE_DOKUMEN_PENDUKUNG'] = '0'

            lines = move.line_ids.filtered(lambda x: x.product_id.id == int(dp_product_id) and x.price_unit < 0)
            #lines = move.line_ids.filtered(lambda x: x.product_id.id == int(dp_product_id) and x.price_unit < 0 and not x.display_type)
            eTax['FG_UANG_MUKA'] = 0
            eTax['UANG_MUKA_DPP'] = int(abs(sum(lines.mapped(lambda l: float_round(l.price_subtotal, 0)))))
            eTax['UANG_MUKA_PPN'] = int(abs(sum(lines.mapped(lambda l: float_round(l.price_total - l.price_subtotal, 0)))))

            fk_values_list = ['FK'] + [eTax[f] for f in FK_HEAD_LIST[1:]]
            # eTax['JALAN'] = move.company_id.partner_id.l10n_id_tax_address or move.company_id.partner_id.street
            # eTax['NOMOR_TELEPON'] = move.company_id.phone or ''
            # eTax['BLOK'] = move.company_id.company_registry or ''
            # lt_values_list = ['FAPR', move.company_id.name] + [eTax[f] for f in LT_HEAD_LIST[3:]]

            # HOW TO ADD 2 line to 1 line for free product
            free, sales = [], []
            #=================DISCOUNT COUPON===============================
            discount_coupon = abs(sum(move.invoice_line_ids.filtered(lambda l: 'Discount:' in l.name and l.price_unit < 0.0).mapped('price_subtotal')))#PASTI MINUS
            discount_ppn_coupon = abs(sum(move.invoice_line_ids.filtered(lambda l: 'Discount:' in l.name and l.price_unit < 0.0).mapped('price_tax')))
            total_units = abs(sum(move.invoice_line_ids.filtered(lambda l: 'Discount:' not in l.name and l.price_unit > 0.0).mapped('price_subtotal')))#TOTAL BUKAN DISKON
            total_ppn_units = abs(sum(move.invoice_line_ids.filtered(lambda l: 'Discount:' not in l.name and l.price_unit > 0.0).mapped('price_tax')))#TOTAL BUKAN DISKON
            #print ('==discount_coupon==',discount_coupon,total_units,discount_ppn_coupon,total_ppn_units)
            tot_line_dpp = sum(int(round(self._amount_currency_line(line.price_subtotal, line),0)) for line in move.invoice_line_ids.filtered(lambda il: il.quantity > 0)) or 0
            tot_line_ppn = sum(int(round(self._amount_currency_line(line.price_tax, line),0)) for line in move.invoice_line_ids.filtered(lambda il: il.quantity > 0)) or 0
            #CHECK TOTAL & LINE TOTALLED
            residual_dpp = amount_untaxed - tot_line_dpp
            residual_ppn = amount_tax - tot_line_ppn
            print ('---DPP--',amount_untaxed,tot_line_dpp,tot_line_dpp-amount_untaxed)
            print ('---PPN--',amount_tax,tot_line_ppn)
            print ('---RESIDUAL--',residual_dpp,residual_ppn,residual_dpp+residual_ppn)
            total_line_dpp = 0.0
            total_line_ppn = 0.0
            #===============================================================
            for line in move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and 'Discount:' not in l.name):
                #===============================================================
                discount_coupon_unit = round((line.price_subtotal / (total_units or 1)) * discount_coupon,0)
                discount_coupon_ppn_unit = round((line.price_tax / (total_ppn_units or 1)) * discount_ppn_coupon,0)
                #===============================================================
                line_dpp = int(round(self._amount_currency_line(line.price_subtotal - discount_coupon_unit, line), 0))
                line_ppn = line.tax_ids and int(round(self._amount_currency_line(line.price_tax - discount_coupon_ppn_unit, line),0))
                print ('===line_dpp,line_ppn===',line_dpp,discount_coupon_unit,line_ppn)
                # line_coupon_ppn = 
                # if move.company_id.discount_efaktur_display == 'no':
                #     HARGA_SATUAN = int(self._amount_currency_line(line.price_subtotal/line.quantity, line)) or '0'
                #     JUMLAH_BARANG = line.quantity or 1
                #     HARGA_TOTAL = int(self._amount_currency_line(line.price_subtotal, line)) or '0'
                #     DISKON = '0'
                #     DPP = line_dpp or '0'
                #     PPN = line_ppn or '0'
                # else:
                #===============================================================
                # *invoice_line_unit_price is price unit use for harga_satuan's column
                # *invoice_line_quantity is quantity use for jumlah_barang's column
                # *invoice_line_total_price is bruto price use for harga_total's column
                # *invoice_line_discount_m2m is discount price use for diskon's column
                # *line.price_subtotal is subtotal price use for dpp's column
                # *tax_line or free_tax_line is tax price use for ppn's column
                free_tax_line = tax_line = bruto_total = total_discount = 0.0

                for tax in line.tax_ids:
                    if tax.amount > 0:
                        tax_line += line.price_subtotal * (tax.amount / 100.0)

                # invoice_line_unit_price = line.price_unit
                # invoice_line_total_price = invoice_line_unit_price * line.quantity  

                discount = 1 - (line.discount / 100)
                # guarantees price to be tax-excluded
                #invoice_line_total_price = line.price_subtotal / discount if discount else 
                DPP = max_line_id == line and line_dpp + residual_dpp or line_dpp or 0
                invoice_line_total_price = DPP
                invoice_line_unit_price = invoice_line_total_price / line.quantity if line.quantity else 0
                HARGA_SATUAN = round(self._amount_currency_line(invoice_line_unit_price, line),2)or '0'
                JUMLAH_BARANG = line.quantity or 1
                HARGA_TOTAL = int(self._amount_currency_line(invoice_line_total_price, line)) or '0'
                #DISKON = int(line.price_discount_untaxed) or '0'
                PPN = max_line_id == line and line_ppn + residual_ppn or line_ppn or 0
                #print ('DPP + PPN',max_line_id.price_unit, line_dpp,' + ',residual_dpp,line_ppn,' + ',residual_ppn)
                # tax_amt_type = sum(tax.amount_type == 'percent' and tax.amount/100.0 or tax.amount for tax in line.tax_ids)
                #===============================================================
                
                line_dict = {
                    'KODE_OBJEK': line.product_id.default_code or '',
                    'NAMA': line.product_id.name + (' ' + line.product_id.product_brand.name) if line.product_id.product_brand else '' or line.product_id.name,#TAMBAH BRAND UTK ADIREKSA
                    'HARGA_SATUAN': HARGA_SATUAN,#int(invoice_line_unit_price),
                    'JUMLAH_BARANG': JUMLAH_BARANG,#line.quantity,
                    'HARGA_TOTAL': DPP,#int(invoice_line_total_price),
                    'DPP': DPP or '0',#int(line.price_subtotal),
                    'product_id': line.product_id.id,
                }
                # print ('===line.price_subtotal==',DPP)
                total_line_dpp += DPP
                if line.price_subtotal < 0:
                    for tax in line.tax_ids:
                        free_tax_line += (line.price_subtotal * (tax.amount / 100.0)) * -1.0

                    line_dict.update({
                        'DISKON': 0,#int(HARGA_TOTAL - line_dpp),
                        'PPN': PPN or 0,#int(free_tax_line),
                    })
                    free.append(line_dict)
                elif line.price_subtotal != 0.0:
                    invoice_line_discount_m2m = HARGA_TOTAL - line_dpp

                    line_dict.update({
                        'DISKON': 0,#int(invoice_line_discount_m2m),
                        'PPN': PPN or 0,#int(tax_line),
                    })
                    sales.append(line_dict)
                total_line_ppn += PPN
                #print ('--line---DPP+PPN-11--',line_dict)
            #print ('===max_line_id==',sales,total_line_dpp-amount_untaxed,total_line_ppn-amount_tax)
            if sales:
                sales[len(sales)-1].update({'HARGA_TOTAL': int(sales[len(sales)-1]['HARGA_TOTAL'] - (total_line_dpp - amount_untaxed)), 'DPP': int(sales[len(sales)-1]['DPP'] - (total_line_dpp - amount_untaxed)), 'PPN': int(sales[len(sales)-1]['PPN'] - (total_line_ppn - amount_tax))})
            #print ('===sales==',sales)
            sub_total_before_adjustment = sub_total_ppn_before_adjustment = 0.0

            # We are finding the product that has affected
            # by free product to adjustment the calculation
            # of discount and subtotal.
            # - the price total of free product will be
            # included as a discount to related of product.
            for sale in sales:
                for f in free:
                    if f['product_id'] == sale['product_id']:
                        sale['DISKON'] = sale['DISKON'] - f['DISKON'] + f['PPN']
                        sale['DPP'] = sale['DPP'] + f['DPP']

                        tax_line = 0

                        for tax in line.tax_ids:
                            if tax.amount > 0:
                                tax_line += sale['DPP'] * (tax.amount / 100.0)

                        sale['PPN'] = int(float_round(tax_line, 0))
                        #print ('==PPN=',tax_line)
                        free.remove(f)

                sub_total_before_adjustment += sale['DPP']
                sub_total_ppn_before_adjustment += sale['PPN']
                bruto_total += sale['DISKON']
                total_discount += float_round(sale['DISKON'], 2)

            output_head += _csv_row(fk_values_list, delimiter)
            for sale in sales:
                of_values_list = ['OF'] + [str(sale[f]) for f in OF_HEAD_LIST[1:-2]] + ['0', '0']
                output_head += _csv_row(of_values_list, delimiter)

        return output_head

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    def _get_price_tax(self):
        for l in self:
            l.price_tax = l.price_total - l.price_subtotal
            
    price_tax = fields.Monetary(string='Tax Amount', compute='_get_price_tax', currency_field='currency_id')
    
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        res = super(AccountMoveLine, self)._get_price_total_and_subtotal_model(price_unit=price_unit, quantity=quantity, discount=discount, currency=currency, product=product, partner=partner, taxes=taxes, move_type=move_type)
        if taxes:
            res['price_tax'] = res['price_total'] - res['price_subtotal']
        else:
            res['price_tax'] = 0.0
        return res