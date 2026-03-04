from odoo import models,api,fields

class ApprovalMatrixDocumentApproval(models.Model):
    _inherit = 'approval.matrix.document.approval'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')