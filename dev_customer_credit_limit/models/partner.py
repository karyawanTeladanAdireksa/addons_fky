# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields

class res_partner(models.Model):
    _inherit= 'res.partner'
    
    def _day_limit_get(self):
        # Bypass Access
        tables, where_clause, where_params = self.sudo().env['account.move.line']._query_get()
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        today = fields.Date.from_string(fields.Date.today())
        self._cr.execute("""SELECT account_move_line.partner_id, act.type, account_move_line.date
                      FROM """+ tables +"""
                      LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE account_move_line.partner_id IN %s
                      AND account_move_line.reconciled IS FALSE              
                      AND ((act.type = 'receivable' AND account_move_line.balance > 0) OR  (act.type = 'payable'  AND account_move_line.balance < 0))
                      """ + where_clause + """
                      ORDER BY account_move_line.date ASC
                      LIMIT 1
                      """, where_params)
      
        datas = self._cr.fetchall()
        if datas:
            for pid, type, val in datas:
                partner = self.browse(pid)
                if type == 'receivable' and val:
                    renew_ml_date = fields.Date.from_string(val)
                    to_limit_day = (today - renew_ml_date).days
                    partner.day_limit = to_limit_day
                else:
                    self.browse(pid).day_limit = 1
        else:
            self.day_limit = 0

    check_credit = fields.Boolean('Check Credit')
    credit_limit_on_hold  = fields.Boolean('Credit limit on hold')
    credit_limit = fields.Float('Credit Limit (Amount)')

    credit_day_limit = fields.Integer('Credit Day(s) Limit', default=1)
    day_limit = fields.Integer(compute='_day_limit_get',
        string='Day Limit', help="Total day this customer owes you.")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: