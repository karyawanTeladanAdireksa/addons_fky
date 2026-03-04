# -*- coding: utf-8 -*- 
# Part of Odoo. See LICENSE file for full copyright and licensing details. 
from odoo import api, fields, models, _
from datetime import datetime 
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    account_force_id = fields.Many2one('account.account',
        'Force Account', help="Choose the accounting at which you want to value the stock "
             "moves created by the inventory instead of the default one",)
    # accounting_date = fields.Date(
    #     'Accounting Date',
    #     help="Choose the accounting date at which you want to value the stock "
    #          "moves created by the inventory instead of the default one (the "
    #          "inventory end date)")
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id.default_account_force_id:
            self.account_force_id = self.partner_id.default_account_force_id.id
            print ('==PARTNER==',self.account_force_id)
        else:
            self.account_force_id = self.picking_type_id.default_force_account.id
            print ('==PICKING TYPE==',self.account_force_id)
    
#     def action_done(self):
#         res = super(StockPicking, self).action_done()
#         acc_pickings = self.filtered(lambda picking: picking.accounting_date)
#         for picking in acc_pickings:
#             res = super(StockPicking, picking.with_context(force_period_date=picking.accounting_date)).action_done()
#         other_pickings = self - acc_pickings
#         if other_pickings:
#             res = super(StockPicking, other_pickings).action_done()
#         return res

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    account_force_id = fields.Many2one('account.account',
        'Force Account', help="Choose the accounting at which you want to value the stock "
             "moves created by the inventory instead of the default one")
    
#     def _account_entry_move(self, qty, description, svl_id, cost):
#         """ Accounting Valuation Entries """
#         return super(StockMove, self.with_context(is_consume_line = self.is_consume_line))._account_entry_move(qty, description, svl_id, cost)
    
#     def _action_done(self):
#         print ('==_action_done==',self._context.get('force_period_date'))
#         moves_todo = super(StockMove, self)._action_done()
#         if moves_todo and self._context.get('force_period_date'):
#             moves_todo.write({'date': self._context.get('force_period_date')})
#         return moves_todo
    
    
#     def _get_price_unit(self):
#         """ Returns the unit price for the move"""
#         self.ensure_one()
#         return super(StockMove, self.with_context(date=self._context.get('force_period_date')))._get_price_unit()

#     def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
#         self.ensure_one()
#         AccountMove = self.env['account.move']
#         quantity = self.env.context.get('forced_quantity', self.product_qty)
#         quantity = quantity if self._is_in() else -1 * quantity
#  
#         # Make an informative `ref` on the created account move to differentiate between classic
#         # movements, vacuum and edition of past moves.
#         ref = self.picking_id.name
#         if self.env.context.get('force_valuation_amount'):
#             if self.env.context.get('forced_quantity') == 0:
#                 ref = 'Revaluation of %s (negative inventory)' % ref
#             elif self.env.context.get('forced_quantity') is not None:
#                 ref = 'Correction of %s (modification of past move)' % ref
#         #DONT CREATE MOVE LINE IF VALUE = 0
#         if self.value:
#             move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value), credit_account_id, debit_account_id)
#             if move_lines:
#                 date = self._context.get('force_period_date', fields.Date.context_today(self))
#                 new_account_move = AccountMove.sudo().create({
#                     'journal_id': journal_id,
#                     'line_ids': move_lines,
#                     'date': date,
#                     'ref': ref,
#                     'stock_move_id': self.id,
#                 })
#                 new_account_move.post()
                
    #===========================================================================
    # CHANGE TO MANAGE BEGINNING BALANCE
    #===========================================================================
    # def _get_accounting_data_for_valuation(self):
    #     """ Return the accounts and journal to use to post Journal Entries for
    #     the real-time valuation of the quant. """
    #     self.ensure_one()
    #     self = self.with_context(force_company=self.company_id.id)
    #     accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
    #     if (self.account_force_id) or (self.picking_id and self.picking_id.account_force_id):
    #         acc_src = self.account_force_id.id or self.picking_id.account_force_id.id
    #     elif (self.account_force_id) or (self.inventory_id and self.inventory_id.account_force_id):
    #         acc_src = self.account_force_id.id or self.inventory_id.account_force_id.id
    #     elif self.location_id.valuation_out_account_id:
    #         acc_src = self.location_id.valuation_out_account_id.id
    #     else:
    #         acc_src = accounts_data['stock_input'].id
        
    #     if (self.account_force_id) or (self.picking_id and self.picking_id.account_force_id):
    #         acc_dest = self.account_force_id.id or self.picking_id.account_force_id.id
    #     elif (self.account_force_id) or (self.inventory_id and self.inventory_id.account_force_id):
    #         acc_dest = self.account_force_id.id or self.inventory_id.account_force_id.id
    #     elif self.location_dest_id.valuation_in_account_id:
    #         acc_dest = self.location_dest_id.valuation_in_account_id.id
    #     else:
    #         acc_dest = accounts_data['stock_output'].id

    #     acc_valuation = accounts_data.get('stock_valuation', False)
    #     if acc_valuation:
    #         acc_valuation = acc_valuation.id
    #     #print ('_get_accounting_data_for_valuation_',journal_id, acc_src, acc_dest, acc_valuation)
    #     if not accounts_data.get('stock_journal', False):
    #         raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
    #     if not acc_src:
    #         raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.display_name))
    #     if not acc_dest:
    #         raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.display_name))
    #     if not acc_valuation:
    #         raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
    #     journal_id = accounts_data['stock_journal'].id
    #     #print ('_get_accounting_data_for_valuation_',journal_id, acc_src, acc_dest, acc_valuation)
    #     return journal_id, acc_src, acc_dest, acc_valuation


    #===========================================================================
    # REPLACE THE BASE ON STOCK_ACCOUNT
    #===========================================================================
    def _get_src_account(self, accounts_data):
        # FILTER SOURCE ACCOUNT WITH account_force_id
        if (self.account_force_id) or (self.picking_id and self.picking_id.account_force_id):
            acc_src = self.account_force_id.id or self.picking_id.account_force_id.id
        # MISSING VALUE inventory_id Odoo 15
        # elif (self.account_force_id) or (self.inventory_id and self.inventory_id.account_force_id):
        #     acc_src = self.account_force_id.id or self.inventory_id.account_force_id.id
        elif self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id
        #return self.location_id.valuation_out_account_id.id or accounts_data['stock_input'].id
        return acc_src

    def _get_dest_account(self, accounts_data):
        #FILTER DESC ACCOUNT WITH account_force_id
        if (self.account_force_id) or (self.picking_id and self.picking_id.account_force_id):
            acc_dest = self.account_force_id.id or self.picking_id.account_force_id.id
        # MISSING VALUE inventory_id Odoo 15
        # elif (self.account_force_id) or (self.inventory_id and self.inventory_id.account_force_id):
        #     acc_dest = self.account_force_id.id or self.inventory_id.account_force_id.id
        elif self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id
        #return self.location_dest_id.valuation_in_account_id.id or accounts_data['stock_output'].id
        return acc_dest
    
    # def _get_accounting_data_for_valuation(self):
    #     """ Return the accounts and journal to use to post Journal Entries for
    #     the real-time valuation of the quant. """
    #     self.ensure_one()
    #     accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
    #     #FOR STOCK MOVE SELF
    #     if (self.account_force_id) or (self.picking_id and self.picking_id.account_force_id):
    #         acc_src = self.account_force_id.id
    #     elif self._context.get('is_consume_line'):
    #         acc_src = accounts_data['income'].id
    #     #'#FOR INITIAL BALANCE #
    #     elif self.inventory_id and self.inventory_id.adjustment_type in ('initial','consume','regular') and self.inventory_id.account_force_id:
    #         acc_src = self.inventory_id.account_force_id.id
    #     #FOR RMA OR ADJUSMENT RETURN TO HPP
    #     elif (self.inventory_id and self.inventory_id.adjustment_type == 'regular' and self.location_id.usage not in ('inventory','production') and self.location_id.valuation_out_account_id):
    #         acc_src = self.location_id.valuation_out_account_id
    #         if not acc_src:
    #             raise UserError(_('Cannot find a stock output account for the location %s. You must define on the location, before processing this operation.') % (self.location_id.name))
    #     #FOR INITIAL BALANCE
    #     elif self.picking_id and self.picking_id.account_force_id and self.picking_id.picking_type_id.code == 'incoming':
    #         #print ('#FOR INITIAL BALANCE #acc_src')
    #         acc_src = self.picking_id.account_force_id.id
    #     elif (self.picking_id and self.picking_id.picking_type_id.code == 'rma-in' and self.location_id.usage not in ('inventory','production')):
    #         #print ('#FOR RMA OR ADJUSMENT RETURN TO HPP #acc_src')
    #         acc_src = accounts_data['expense'].id
    #         if not acc_src:
    #             raise UserError(_('Cannot find a stock output account for the location %s. You must define on the location, before processing this operation.') % (self.location_id.name))
    #     #FOR RECEIVABLE / PAYABLE
    #     elif self.inventory_id and self.inventory_id.adjustment_type in ('out_invoice','in_invoice') and self.location_id.usage in ('inventory','production'):
    #         #print ('#FOR RECEIVABLE / PAYABLE #acc_src')
    #         acc_src = accounts_data['stock_input'].id
    #     #FOR NORMAL ONLY
    #     elif self.location_id.valuation_out_account_id:
    #         #print ('#FOR NORMAL ONLY #acc_src')
    #         acc_src = self.location_id.valuation_out_account_id.id
    #     #FOR INCOMING SHIPMENT
    #     else:
    #         #print ('#FOR INCOMING SHIPMENT #acc_src',self.picking_id.picking_type_id.code,self.location_id.usage)
    #         acc_src = accounts_data['stock_input'].id
    #
    #     #FOR INITIAL BALANCE
    #     if (self.account_force_id) or (self.picking_id and self.picking_id.account_force_id):
    #         acc_dest = self.account_force_id.id
    #     elif self._context.get('is_consume_line'):
    #         acc_dest = accounts_data['expense'].id
    #     elif self.inventory_id and self.inventory_id.adjustment_type in ('initial','consume','regular') and self.inventory_id.account_force_id:
    #         acc_dest = self.inventory_id.account_force_id.id
    #     #FOR ADJUSMENT OR RMA RETURN TO HPP
    #     elif (self.inventory_id and self.inventory_id.adjustment_type == 'regular' and self.location_dest_id.usage not in ('inventory','production') and self.location_dest_id.valuation_in_account_id):
    #         acc_dest = self.location_dest_id.valuation_in_account_id
    #         if not acc_dest:
    #             raise UserError(_('Cannot find a stock input account for the location %s. You must define on the location, before processing this operation.') % (self.location_dest_id.name))
    #     #FOR INITIAL BALANCE
    #     elif self.picking_id and self.picking_id.account_force_id and self.picking_id.picking_type_id.code == 'outgoing':
    #         #print ('#FOR INITIAL BALANCE #acc_src')
    #         acc_dest = self.picking_id.account_force_id.id
    #     elif (self.picking_id and self.picking_id.picking_type_id.code == 'rma-out' and self.location_dest_id.usage not in ('inventory','production')):
    #         acc_dest = accounts_data['expense'].id
    #         if not acc_dest:
    #             raise UserError(_('Cannot find a stock input account for the location %s. You must define on the location, before processing this operation.') % (self.location_dest_id.name))
    #     #FOR RECEIVABLE / PAYABLE
    #     elif self.inventory_id and self.inventory_id.adjustment_type in ('out_invoice','in_invoice') and self.location_dest_id.usage in ('inventory','production'):
    #         acc_dest = accounts_data['stock_output'].id
    #     #FOR NORMAL ONLY
    #     elif self.location_dest_id.valuation_in_account_id:
    #         acc_dest = self.location_dest_id.valuation_in_account_id.id
    #     #FOR OUTGOING SHIPMENT
    #     else:
    #         acc_dest = accounts_data['stock_output'].id
    #
    #     acc_valuation = accounts_data.get('stock_valuation', False)
    #     if acc_valuation:
    #         acc_valuation = acc_valuation.id
    #     print ('_get_accounting_data_for_valuation_',journal_id, acc_src, acc_dest, acc_valuation)
    #     if not accounts_data.get('stock_journal', False):
    #         raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))
    #     if not acc_src:
    #         raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
    #     if not acc_dest:
    #         raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (self.product_id.name))
    #     if not acc_valuation:
    #         raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
    #     journal_id = accounts_data['stock_journal'].id
    #     return journal_id, acc_src, acc_dest, acc_valuation
    

# class StockMoveLine(models.Model):
#     _inherit = 'stock.move.line'
# 
#     def _action_done(self):
#         moves_line_todo = super(StockMoveLine, self)._action_done()
#         for line in self:
#             if line and self._context.get('force_period_date'):
#                 line.write({'date': self._context.get('force_period_date')})
#         return moves_line_todo