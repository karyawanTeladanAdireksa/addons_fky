
import stdnum
from stdnum.eu.vat import check_vies
from stdnum.exceptions import InvalidComponent, InvalidChecksum, InvalidFormat
from stdnum.util import clean
from stdnum import luhn
from odoo import models, fields, api
from collections import defaultdict

class ResCountry(models.Model):
    _inherit = 'res.country'

    coretax_code = fields.Char('Coretax Code')

class Partner(models.Model):
    _inherit = "res.partner"
    
    tax_calculation_coretax = fields.Char(string='Tax calculation other', default='11/12')
    coretax_type = fields.Selection([
        ('TIN','TIN'),
        ('National ID','National ID'),
        ('Passport','Passport'),
        ('Other ID','Other ID')
    ], string="Coretax ID Type")
    l10n_id_need_kode_transaksi = fields.Boolean()
    l10n_id_passport = fields.Char(string='Passport')
    l10n_id_other = fields.Char(string='Other ID')

    #OVERIDE CHECK VAT ID
    def check_vat_id(self, vat):
        """ Temporary Indonesian VAT validation to support the new format
        introduced in January 2024."""
        vat = clean(vat, ' -.').strip()
        if len(vat) not in (15, 16) or not vat[0:15].isdecimal() or not vat[-1].isdecimal():
            return False

        print ('# VAT is only digits and of the right length, check the Luhn checksum.',vat)
        # try:
        #     luhn.validate(vat[0:10])
        # except (InvalidFormat, InvalidChecksum):
        #     return False

        return True

    @api.model
    def _get_default_coretax_address_format(self):
        return "%(street)s %(street2)s %(city)s %(state_code)s %(zip)s %(country_name)s"

    @api.model
    def _get_coretax_address_format(self):
        return self._get_default_coretax_address_format()

    def _prepare_display_coretax_address(self, without_company=False):
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_coretax_address_format()
        args = defaultdict(str, {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
        })
        for field in self._formatting_address_fields():
            args[field] = self[field] or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s, ' + address_format
        return address_format, args

    def _display_coretax_address(self, without_company=False):
        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param without_company: if address contains company
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        address_format, args = self._prepare_display_coretax_address(without_company)
        return address_format % args
        