# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError

# dynamic label
class ReportBarcodePrint(models.AbstractModel):
    _name = 'report.dynamic_barcode_labels.report_dynamic_label'
    _description = 'Barcode Report'

    @api.model
    def _get_report_values(self, docids, data=None):
       docs = self.env['dynamic.label.wizard'].browse(docids)
    #    report = docs._get_report_from_name('dynamic_barcode_labels.report_product_label_57x35')
       return {
            'doc_ids' : docids, 
            'doc_model' : 'dynamic.label.wizard',
            'data' : data['form']['data_values'],
            'docs' : docs,
        }


# dynamic label mini
class ReportBarcodePrint(models.AbstractModel):
    _name = 'report.dynamic_barcode_labels.report_dynamic_label_mini'
    _description = 'Barcode Report'

    @api.model
    def _get_report_values(self, docids, data=None):
       
       docs = self.env['dynamic.label.wizard'].browse(docids)
       return {
                'doc_ids' : docids,
                'doc_model' : 'dynamic.label.wizard',
                'data' : data['form']['data_values'],
                'docs' : docs,
            }