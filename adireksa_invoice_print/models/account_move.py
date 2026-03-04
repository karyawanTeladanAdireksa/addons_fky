from odoo import models, fields, api,_
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

# OVERRIDE FUNCTION ACTION_PRINT
    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        if self.user_has_groups('account.group_account_invoice'):
            return self.env.ref('adireksa_invoice_print.action_report_adireksa_original_invoice_copy').report_action(self)
        else:
            return self.env.ref('account.account_invoices_without_payment').report_action(self)
     
# OVERRIDE GET REPORT INVOICE
    # def _get_name_invoice_report(self):
    #     """ This method need to be inherit by the localizations if they want to print a custom invoice report instead of
    #     the default one. For example please review the l10n_ar module """
    #     self.ensure_one()
    #     return 'adireksa_invoice_print.report_invoice_adireksa_document_copy'