from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime
import logging



class OriginalInvoiceReport(models.AbstractModel):
    _name = 'report.adireksa_invoice_print.report_invoice_adireksa'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Original Invoice'


    @api.model
    def create_log_note(self, record):

        log_message = f"Original Invoice Downloaded By {self.env.user.name} At {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        record.message_post(body=log_message)


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)

        
        if data and 'form' in data:
            data_values = data['form'].get('data_values')
        else:
            data_values = {}

        for doc in docs:
            self.create_log_note(doc)

        
        return {
            'doc_ids' : docids, 
            'doc_model' : 'account.move',
            'data' : data_values,
            'docs' : docs,
        } 
