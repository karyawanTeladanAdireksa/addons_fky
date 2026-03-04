# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import ast
import random
from datetime import datetime, timedelta
from odoo.release import version

from babel.dates import format_datetime, format_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang
from odoo import fields, models, api, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_voucher = fields.Boolean('Show on Voucher')

    # def _kanban_dashboard_graph(self):
    #     for journal in self:
    #         if (journal.type in ['sale', 'purchase']):
    #             journal.kanban_dashboard_graph = json.dumps(journal.get_bar_graph_datas())
    #         elif (journal.type in ['cash', 'bank']):
    #             if journal.is_voucher:
    #                 journal.kanban_dashboard_graph = json.dumps(journal.get_line_graph_datas())
    #             else:
    #                 journal.kanban_dashboard_graph = json.dumps(journal.get_line_graph_datas())
    #         else:
    #             journal.kanban_dashboard_graph = False

    def cashbox_action_with_context(self):
        action_name = self.env.context.get('action_name', False)
        if not action_name:
            return False
        ctx = dict(self.env.context, default_journal_id=self.id)
        if ctx.get('search_default_journal', False):
            ctx.update(search_default_journal_id=self.id)
            ctx['search_default_journal'] = False  # otherwise it will do a useless groupby in bank statements
        ctx.pop('group_by', None)
        action = self.env['ir.actions.act_window']._for_xml_id(f"aos_account_voucher.{action_name}")
        action['context'] = ctx
        if ctx.get('use_domain', False):
            #action['domain'] = isinstance(ctx['use_domain'], list) and ctx['use_domain'] or ['|', ('journal_id', '=', self.id), ('journal_id', '=', False)]
            action['name'] = _(
                "%(action)s for journal %(journal)s",
                action=action["name"],
                journal=self.name,
            )
        return action

    def _get_last_voucher_statement(self, domain=None):
        ''' Retrieve the last bank statement created using this journal.
        :param domain:  An additional domain to be applied on the account.bank.statement model.
        :return:        An account.bank.statement record or an empty recordset.
        '''
        self.ensure_one()
        last_statement_domain = (domain or []) + [('payment_journal_id', '=', self.id)]
        last_statement = self.env['account.voucher'].search(last_statement_domain, order='date desc, id desc', limit=1)
        return last_statement

    def get_line_graph_datas(self):
        result = super(AccountJournal, self).get_line_graph_datas()
        if not self.is_voucher:
            # print ('#KLO BUKAN VOUCHER PAKE LAMA')
            return result
        else:
            # print ('#KLO VOUCHER BARU INI')
            return self.get_voucher_line_graph_datas()
        # return [{'values': data, 'title': graph_title, 'key': graph_key, 'area': True, 'color': color, 'is_sample_data': 0}]
    # Below method is used to get data of bank and cash statemens
    def get_voucher_line_graph_datas(self):
        """Computes the data used to display the graph for bank and cash journals in the accounting dashboard"""
        currency = self.currency_id or self.company_id.currency_id

        def build_graph_data(date, amount):
            #print ('--build_graph_data--',date,amount,currency)
            #display date in locale format
            #amount = formatLang(self.env, amount or 0.0, currency_obj=self.currency_id or self.company_id.currency_id)
            name = format_date(date, 'd LLLL Y', locale=locale)
            short_name = format_date(date, 'd MMM', locale=locale)
            return {'x':short_name, 'y': amount, 'name':name}

        self.ensure_one()
        # BankStatement = self.env['account.bank.statement']
        data = []
        today = datetime.today()
        last_month = today + timedelta(days=-30)
        locale = get_lang(self.env).code

        #starting point of the graph is the last statement
        # last_stmt = self._get_last_voucher_statement(domain=[('state', 'in', ['confirm', 'approved', 'in_payment', 'posted'])])

        #last_balance = last_stmt and last_stmt.balance_end_real or 0

        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }
        res = {}
        accounts = self.default_account_id
        context_balance_start = {'strict_range': True, 'date_to': today.strftime(DF), 'account_ids': self.default_account_id}#'date_to': self.date_to{'strict_range': True, 'initial_bal': True, 'date_from': self.date_from, 'date_to': False}
        tables, where_clause, where_params = self.env['account.move.line'].with_context(context_balance_start)._query_get()
        #print ('===tables==',tables,where_clause, where_params)
        tables = tables.replace('"', '') if tables else "account_move_line"
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                    " FROM " + tables + \
                    " WHERE account_id IN %s " \
                        + filters + \
                    " GROUP BY account_id"
        params = (tuple(accounts._ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            res[row['id']] = row
        #print ('===RES===',res)
        beginning_balance = 0
        query_result = []
        if res.get(self.default_account_id.id):
            beginning_balance = res[self.default_account_id.id]['balance']
            #print ('==res==',res, last_month, beginning_balance)
            data.append(build_graph_data(last_month, beginning_balance))

            #then we subtract the total amount of bank statement lines per day to get the previous points
            #(graph is drawn backward)
            date = today
            amount = beginning_balance
            query = '''
                SELECT move.date, sum(move.debit - move.credit) as amount
                FROM account_move_line move
                WHERE move.account_id = %s
                AND move.date > %s
                GROUP BY move.date
                ORDER BY move.date desc
            '''
            #print ('===query==',query,self.id, last_month, today)
            self.env.cr.execute(query, (self.default_account_id.id, today))
            query_result = self.env.cr.dictfetchall()
            for val in query_result:
                date = val['date']
                if date != today.strftime(DF):  # make sure the last point in the graph is today
                    data[:0] = [build_graph_data(today, amount)]
                amount = currency.round(amount + val['amount'])
                data.append(build_graph_data(date, amount))
        # make sure the graph starts 1 month ago
        # if date.strftime(DF) != today.strftime(DF):
        #     data[:0] = [build_graph_data(today, amount)]

        [graph_title, graph_key] = self._graph_title_and_key()
        color = '#875A7B' if 'e' in version else '#7c7bad'

        is_sample_data = not beginning_balance and len(query_result) == 0
        if is_sample_data:
            data = []
            for i in range(30, 0, -5):
                current_date = today + timedelta(days=-i)
                data.append(build_graph_data(current_date, random.randint(-5, 15)))

        return [{'values': data, 'title': graph_title, 'key': graph_key, 'area': True, 'color': color, 'is_sample_data': is_sample_data}]

    def _get_vouchers_to_pay_query(self):
        """
        Returns a tuple containing as it's first element the SQL query used to
        gather the expenses in reported state data, and the arguments
        dictionary to use to run it as it's second.
        """
        states = self.env.context.get('states') or ['confirm', 'in_payment']
        query = """SELECT amount as amount_total, currency_id AS currency
                  FROM account_voucher
                  WHERE state IN %(states)s and voucher_type = 'purchase'
                  and payment_journal_id = %(payment_journal_id)s"""
        return (query, {'states': tuple(states), 'payment_journal_id': self.id})


    def _get_vouchers_to_receipt_query(self):
        """
        Returns a tuple containing as it's first element the SQL query used to
        gather the expenses in reported state data, and the arguments
        dictionary to use to run it as it's second.
        """
        states = self.env.context.get('states') or ['confirm', 'in_payment']
        query = """SELECT amount as amount_total, currency_id AS currency
                  FROM account_voucher
                  WHERE state IN %(states)s and voucher_type = 'sale'
                  and payment_journal_id = %(payment_journal_id)s"""
        return (query, {'states': tuple(states), 'payment_journal_id': self.id})

    def get_journal_dashboard_datas(self):
        res = super(AccountJournal, self).get_journal_dashboard_datas()
        #add the number and sum of expenses to pay to the json defining the accounting dashboard data
        states = self.env.context.get('states') or []
        #PAYMENT
        (query, query_args) = self.with_context(states=states)._get_vouchers_to_pay_query()
        self.env.cr.execute(query, query_args)
        query_results_to_pay = self.env.cr.dictfetchall()
        (number_to_pay, sum_to_pay) = self._count_results_and_sum_amounts(query_results_to_pay, self.company_id.currency_id)
        #RECEIPT
        (query, query_args) = self.with_context(states=states)._get_vouchers_to_receipt_query()
        self.env.cr.execute(query, query_args)
        query_results_to_receipt = self.env.cr.dictfetchall()
        (number_to_receipt, sum_to_receipt) = self._count_results_and_sum_amounts(query_results_to_receipt, self.company_id.currency_id)

        bank_account_balance, nb_lines_bank_account_balance = self._get_journal_bank_account_balance(domain=[('parent_state', '=', 'posted')])
        res['number_vouchers_to_pay'] = number_to_pay
        res['sum_vouchers_to_pay'] = formatLang(self.env, sum_to_receipt - sum_to_pay or 0.0, currency_obj=self.currency_id or self.company_id.currency_id)
        res['sum_vouchers_balance'] = formatLang(self.env, (bank_account_balance + (sum_to_receipt - sum_to_pay)) or 0.0, currency_obj=self.currency_id or self.company_id.currency_id)
        return res

    def open_voucher_with_context(self):
        action_name = self.env.context.get('action_name', False)
        if not action_name:
            return False
        ctx = dict(self.env.context, default_payment_journal_id=self.id)
        #print ('===open_voucher_with_context===',action_name,self.id)
        if ctx.get('search_default_payment_journal_id', False):
            ctx.update(search_default_payment_journal_id=self.id)
            ctx['search_default_payment_journal_id'] = False  # otherwise it will do a useless groupby in bank statements
        ctx.pop('group_by', None)
        action = self.env['ir.actions.act_window']._for_xml_id(f"aos_account_voucher.{action_name}")
        action['context'] = ctx
        # if ctx.get('use_domain', False):
        action['domain'] = []
        if self.env.context.get('voucher_type', False):
            action['domain'] += [('voucher_type','=',self.env.context.get('voucher_type', 'purchase'))]
        action['domain'] += ['|', ('payment_journal_id', '=', self.id), ('payment_journal_id', '=', False)]
        action['name'] = _(
            "%(action)s for journal %(journal)s",
            action=action["name"],
            journal=self.name,
        )
        return action

    def create_voucher_payment(self):
        """return action to create a customer payment"""
        return self.open_vouchers_action('purchase', mode='form')

    def create_voucher_receipt(self):
        """return action to create a supplier payment"""
        return self.open_vouchers_action('sale', mode='form')

    def open_vouchers_action(self, voucher_type, mode='tree'):
        if voucher_type == 'sale':
            action_ref = 'aos_account_voucher.action_review_voucher_list_aos_voucher'
        elif voucher_type == 'purchase':
            action_ref = 'aos_account_voucher.action_receipt_voucher_list_aos_voucher'
        else:
            action_ref = 'account.action_account_payments'
        action = self.env['ir.actions.act_window']._for_xml_id(action_ref)
        action['context'] = dict(ast.literal_eval(action.get('context')), default_payment_journal_id=self.id, search_default_payment_journal_id=self.id)
        # if voucher_type == 'transfer':
        #     action['context'].update({
        #         'default_partner_id': self.company_id.partner_id.id,
        #         'default_is_internal_transfer': True,
        #     })
        if mode == 'form':
            action['views'] = [[False, 'form']]
        return action

class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    date = fields.Date('Date')


class AccountCashboxLine(models.Model):
    _inherit = 'account.cashbox.line'