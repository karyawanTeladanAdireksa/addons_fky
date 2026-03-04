from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def remove_sales_return(self):
        to_removes = [
            'sales.return',
            'sales.return.line',
        ]
        seqs = [
            'aos_sales_return',
        ]
        return self.remove_app_data(to_removes, seqs)

    def remove_sale_agreement(self):
        to_removes = [
            'sale.agreement',
            'sale.agreement.line',
        ]
        seqs = [
            'aos_sales_agreement',
        ]
        return self.remove_app_data(to_removes, seqs)
    
    
    def remove_credit_limit_request(self):
        to_removes = [
            'credit.limit.request',
        ]
        seqs = [
            'aos_credit_limit_request',
        ]
        return self.remove_app_data(to_removes, seqs)
    
    
    def remove_cashback_transaction(self):
        to_removes = [
            'cashback.lines',
            'automatic.cashback.lines',
            'manual.cashback.lines',
            'cashback.used.lines',
            'cashback.internal.category.lines',
            'cashback.product.lines',
            'cashback.manual',
            'cashback.invoice',  
        ]
        seqs = [
            'aos_cashback',
        ]
        return self.remove_app_data(to_removes, seqs)