from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_after_ppn = fields.Monetary(string="Total Before Ppn" ,compute="_compute_total")
    discount_total_bef_ppn = fields.Monetary(string="Discount Total PPN",compute="_compute_discount_total")
    cashback_total_ppn = fields.Monetary(string="Cashback Total PPN",compute="_compute_cashback_total")
    # amount_total_all = fields.Monetary(string="Total",compute="_compute_total_all",store=True) 

    # COMPUTE AMOUNT TOTAL AFTER PPN
    @api.depends('invoice_line_ids.after_ppn_subtotal')
    def _compute_total(self):
        for record in self:
            # Total Price Amount after ppn and discount
            price_amount = sum(record.invoice_line_ids.filtered(lambda x:x.is_reward_line == False).mapped('after_ppn_subtotal'))  
            record.amount_after_ppn = price_amount if record.invoice_line_ids else 0.0

    
    
    # COMPUTE DISCOUNT SEBELUM PPN
    @api.depends('invoice_line_ids.discount')
    def _compute_discount_total(self):
        for rec in self :
            rec.discount_total_bef_ppn = rec.discount_total / 1.11
    
    
    @api.depends('invoice_line_ids.cashback_percent')
    def _compute_cashback_total(self):
        for rec in self :
            rec.cashback_total_ppn = rec.cashback_total
    


    #COMPUTE TOTAL TAX        
    # @api.depends('invoice_line_ids.before_ppn_subtotal')
    # def _compute_total_all(self):
    #     for record in self :
    #         total = record.amount_after_ppn - record.discount_total_bef_ppn - record.cashback_total_pivot
    #         record.amount_total_all = total




class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # price_after_ppn = fields.Monetary(string='Price After PPN',compute="_compute_price_after",store=True)
    after_ppn_subtotal = fields.Monetary(string="After Ppn Subtotal",compute="_compute_price_total")     

    @api.depends('quantity','price_unit')
    def _compute_price_total(self):
        for line in self:
            # price = line.price_unit * line.quantity 
            # price_after_ppn = price + (price / 100 * 11)
            line.after_ppn_subtotal = line.price_unit * line.quantity 
        


