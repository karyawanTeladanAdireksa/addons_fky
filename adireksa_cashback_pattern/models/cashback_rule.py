# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import math
import calendar

import logging
_logger = logging.getLogger(__name__)


# class ResPartnerCategory(models.Model):
#     _inherit = 'res.partner.category'
#
#     wilayah = fields.Selection([
#         ('area1','Wilayah I (Jawa, Lampung, Palembang)'),
#         ('area2','Wilayah II (selain Jawa, Lampung, Palembang)'),
#         ], string='Wilayah', default='area1')
#

# res.partner.category to customer.category
class ResPartnerCategory(models.Model):
    _name = 'customer.group'
    _rec_name = 'name'
    _description = 'Customer Group'

    name = fields.Char(string="Group Name", required=False, )
    wilayah = fields.Selection([
            ('area1','Wilayah I (Jawa, Lampung, Palembang)'),
            ('area2','Wilayah II (selain Jawa, Lampung, Palembang)'),
            ], string='Wilayah', default='area1')
    
    customer_ids = fields.One2many(comodel_name="res.partner", inverse_name="group_id", string="", required=False, )

class ResPartner(models.Model):
    _inherit = 'res.partner'

    group_id = fields.Many2one(comodel_name="customer.group", string="Customer Group", required=False, )


class CashbackRule(models.Model):
    _name = 'cashback.rule'
    _inherit = ['mail.thread']
    _description = 'Cashback Rule'

    name = fields.Char(string='Name')
    state = fields.Selection([('draft','Draft'),('approve','Approved'),('cancel','Cancelled')], 
        string='Status', default='draft', track_visibility='onchange')
    active = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', track_visibility='onchange')
    period = fields.Integer(string='Year', track_visibility='onchange')
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many('cashback.rule.line', 'rule_id', string='Rule Lines', copy=True)
    cron_ids = fields.Many2many('ir.cron', string='Schedule Actions')

    @api.constrains('period')
    def _check_period(self):
        for record in self:
            year = datetime.today().strftime('%Y')
            check_rule = self.env['cashback.rule'].search([('state','=','approve'),
                ('period','=',year),('id','!=',record.id),('company_id','=',record.company_id.id)])
            if check_rule:
                raise ValidationError("Please input another year, this year rule has already been assigned.")

    def get_quarter_month(self, month):
        if month >= 1 and month <= 3: # Quarter 1
            start_month = 1
            end_month = 3
            status = 'q1'
        elif month >= 4 and month <= 6: # Quarter 2
            start_month = 4
            end_month = 6
            status = 'q2'
        elif month >= 7 and month <= 9: # Quarter 3
            start_month = 7
            end_month = 9
            status = 'q3'
        elif month >= 10 and month <= 12: # Quarter 4
            start_month = 10
            end_month = 12
            status = 'q4'
        return start_month, end_month, status

    def get_half_month(self, month):
        if month >= 1 and month <= 6: # Quarter 1
            start_month = 1
            end_month = 6
            status = 'firsthalf'
        elif month >= 7 and month <= 12: # Quarter 2
            start_month = 7
            end_month = 12
            status = 'secondhalf'
        return start_month, end_month, status

    def compute_date_range(self, date, frequency):
        if frequency == 'annual': # Annual
            dfrom = '%d-%d-%d' % (date.year, 1, 1)
            dto = '%d-%d-%d' % (date.year, 12, 31)
        elif frequency == '6month': # 6 Month
            start_month, end_month, status = self.get_half_month(date.month)
            dfrom = '%d-%d-%d' % (date.year, start_month, 1)
            dto = '%d-%d-%d' % (date.year, end_month, calendar.mdays[end_month])
        elif frequency == 'quarter': # Quarterly
            start_month, end_month, status = self.get_quarter_month(date.month)
            dfrom = '%d-%d-%d' % (date.year, start_month, 1)
            dto = '%d-%d-%d' % (date.year, end_month, calendar.mdays[end_month])
        elif frequency == 'month': # Monthly
            dfrom = '%d-%d-%d' % (date.year, date.month, 1)
            dto = '%d-%d-%d' % (date.year, date.month, calendar.mdays[date.month])
        return dfrom, dto

    def action_approve(self):
        date = datetime.today()
        self.write({'state': 'approve'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def compute_annual_cashback(self):
        cr = self.env.cr
        freq = 'annual'
        cr.execute("""SELECT frequency FROM cashback_rule_line
            WHERE frequency = '{1}' and rule_id = {0} 
            group by frequency order by frequency""".format(self.id, freq))
        if len(cr.fetchall()) <= 0:
            raise UserError("This cashback rule don't have Annually formula!")
        self.cron_automate_cashback_in(freq)

    def compute_6month_cashback(self):
        cr = self.env.cr
        freq = '6month'
        cr.execute("""SELECT frequency FROM cashback_rule_line
            WHERE frequency = '{1}' and rule_id = {0} 
            group by frequency order by frequency""".format(self.id, freq))
        if len(cr.fetchall()) <= 0:
            raise UserError("This cashback rule don't have 6 Month formula!")
        self.cron_automate_cashback_in(freq)

    def compute_quarter_cashback(self):
        cr = self.env.cr
        freq = 'quarter'
        today = datetime.today()
        dfrom, dto = self.compute_date_range(today, freq)
        cr.execute("""SELECT frequency FROM cashback_rule_line
            WHERE frequency = '{1}' and rule_id = {0} 
            group by frequency order by frequency""".format(self.id, freq))
        if len(cr.fetchall()) <= 0:
            raise UserError("This cashback rule don't have Quarterly formula!")
        self.cron_automate_cashback_in(freq)

    def compute_month_cashback(self):
        cr = self.env.cr
        freq = 'month'
        cr.execute("""SELECT frequency FROM cashback_rule_line
            WHERE frequency = '{1}' and rule_id = {0} 
            group by frequency order by frequency""".format(self.id, freq))
        if len(cr.fetchall()) <= 0:
            raise UserError("This cashback rule don't have Monthly formula!")
        self.cron_automate_cashback_in(freq)

    def compute_revenue(self, group_id, cid, frequency):
        cr = self.env.cr
        today = datetime.today()
        if frequency == 'annual':
            date = today + relativedelta(years=-1)
            status = 'annual'
        elif frequency == '6month':
            start, end, status = self.get_half_month(today.month)
            if start == 1:
                quarter_year = today.year - 1
                quarter_month = 7
                status = 'secondhalf'
            else: # Get previous status if button clicked
                quarter_year = today.year
                quarter_month = start - 6
                status = 'secondhalf' if status == 'firsthalf' else 'firsthalf'
            date = datetime(quarter_year, quarter_month, 1)
        elif frequency == 'quarter':
            start, end, status = self.get_quarter_month(today.month)
            if start == 1:
                quarter_year = today.year - 1
                quarter_month = 10
                status = 'q4'
            else: # Get previous status if button clicked
                quarter_year = today.year
                quarter_month = start - 3
                if status == 'q2':
                    status = 'q1'
                elif status == 'q3':
                    status = 'q2'
                elif status == 'q4':
                    status = 'q3'
            date = datetime(quarter_year, quarter_month, 1)
        elif frequency == 'month':
            date = today + relativedelta(months=-1)
            status = 'month'
        dfrom, dto = self.compute_date_range(date, frequency)
        period1 = datetime.strptime(dfrom, '%Y-%m-%d')
        period2 = datetime.strptime(dto, '%Y-%m-%d')
        cr.execute("""SELECT COALESCE(SUM(ai.amount_total), 0) as revenue FROM account_invoice ai
            inner join res_partner_res_partner_category_rel rpc on rpc.partner_id = ai.partner_id
            inner join master_customer_cashback mcc on mcc.group_id = rpc.category_id 
            where ai.state in ('open','paid') and mcc.group_id = {0} and mcc.company_id = {1} and ai.company_id = {1} 
            and mcc.state = 'confirm' and ai.date_invoice between '{2}' and '{3}'""".format(group_id, cid, dfrom, dto))
        rev = cr.dictfetchone()
        revenue = math.ceil(rev['revenue']) if rev else 0.0
        if status not in ['month','annual']:
            whr = """and ctl.frequency = '{0}' and ct.period = {1} and ctl.month1 = {2} 
                and ctl.month2 = {3}""".format(frequency, period1.year, period1.month, period2.month)
        else:
            whr = "and ctl.frequency = '{0}' and ct.period = '{1}'".format(frequency, period1.year)
        cr.execute("""SELECT COALESCE(sum(ctl.amount), 0) as target FROM adireksa_customer_target ct
            inner join adireksa_customer_target_line ctl on ctl.target_id = ct.id 
            where ct.group_id = {0} and ct.company_id = {1} and ctl.state = 'approve' {2}""".format(group_id, cid, whr))
        tgt = cr.dictfetchone()
        target = tgt['target'] if tgt else 0.0
        return revenue, target, dto, status

    def get_auto_cashback_ref(self, status):
        if status == 'q1':
            title = 'Quarter 1'
            month_range = 'Januari s/d Maret'
        elif status == 'q2':
            title = 'Quarter 2'
            month_range = 'April s/d Juni'
        elif status == 'q3':
            title = 'Quarter 3'
            month_range = 'Juli s/d September'
        elif status == 'q4':
            title = 'Quarter 4'
            month_range = 'October s/d Desember'
        elif status == 'firsthalf':
            title = '6 Month'
            month_range = 'Januari s/d Juni'
        elif status == 'secondhalf':
            title = '6 Month'
            month_range = 'Juli s/d Desember'
        else:
            title = ''
            month_range = ''
        return title, month_range

    def compute_cashback_in(self, data, group_id, frequency, revenue, target, status):
        cr = self.env.cr
        total = 0.0
        ref = ''
        line_id = []
        title, month_range = self.get_auto_cashback_ref(status)
        if frequency == 'annual':
            actual_target = data.target_modifier * target
            if data.trigger == 'revenue' and revenue >= actual_target:
                total = (data.formula / 100) * (revenue - target)
                # ref = data.name
                ref = 'Omzet Periode Annual (Januari s/d Desember) Hit Target, Total Invoice: Rp. %s' % ('{:0,.0f}'.format(revenue))
                line_id.append(data.id)
        elif frequency == '6month':
            actual_target = data.target_modifier * target
            if data.trigger == 'revenue' and revenue >= actual_target:
                total = (data.formula / 100) * (revenue - target)
                # ref = data.name
                ref = 'Omzet Periode %s (%s) Hit Target, Total Invoice: Rp. %s' % (title, month_range, '{:0,.0f}'.format(revenue))
                line_id.append(data.id)
        elif frequency =='quarter':
            actual_target = data.target_modifier * target
            if data.trigger == 'revenue' and revenue >= actual_target:
                total = (data.formula / 100) * (revenue - target)
                # ref = data.name
                ref = 'Omzet Periode %s (%s) Hit Target, Total Invoice: Rp. %s' % (title, month_range, '{:0,.0f}'.format(revenue))
                line_id.append(data.id)
        elif frequency == 'month':
            total_class = 0.0
            total_area = 0.0
            ref_class = ''
            ref_area = ''
            for x in data:
                if x.get('sub_type') == 'class' and x.get('trigger') == 'sales':
                    if x.get('range') > 0.0 and revenue >= x.get('target') and revenue < x.get('range'):
                        total_class = (x.get('formula') / 100) * revenue
                        ref_class= x.get('name')
                        line_id.append(x.get('id'))
                    elif x.get('range') == 0.0  and revenue >= x.get('target') :
                        total_class = (x.get('formula') / 100) * revenue
                        ref_class = x.get('name')
                        line_id.append(x.get('id'))
                # Subsidi Ongkir dengan wilayah
                cr.execute("""SELECT wilayah FROM res_partner_category WHERE id={0}""".format(group_id))
                res = cr.dictfetchone()
                area = res['wilayah'] if res else False
                if area and x.get('sub_type') == area and x.get('trigger') == 'sales' and revenue >= x.get('target'):
                    total_area = (x.get('formula') / 100) * revenue
                    ref_area = ' dan  %s' % (x.get('name'))
                    line_id.append(x.get('id'))
            total = total_class + total_area
            ref = ref_class + ref_area
        return math.ceil(total), ref, line_id

    def check_duplicated_cashback(self, freq, group_id, date):
        cr = self.env.cr
        dfrom, dto = self.compute_date_range(datetime.strptime(date, '%Y-%m-%d'), freq)
        cnt = False
        # Do not create cashback if there is approved cashback on specific period
        cr.execute("""SELECT count(mcc.id) as total FROM automatic_cashback_lines acl
            INNER JOIN master_customer_cashback mcc ON mcc.id = acl.cashback_id 
            INNER JOIN automatic_cashback_rule_rel ar ON ar.automatic_cashback_lines_id = acl.id 
            INNER JOIN cashback_rule_line crl ON crl.id = ar.cashback_rule_line_id
            WHERE acl.date between '{0}' and '{1}' and acl.state = 'approve' 
            and crl.rule_id = {2} and mcc.group_id = {3} and crl.frequency = '{4}' 
            GROUP BY mcc.id""".format(dfrom, dto, self.id, group_id, freq))
        res = cr.dictfetchone()
        if res and res['total'] > 0:
            cnt = True
        # Delete cashback if there are multiple cashbacks that has waiting_for_approval status
        cr.execute("""SELECT acl.id FROM automatic_cashback_lines acl
            INNER JOIN master_customer_cashback mcc ON mcc.id = acl.cashback_id 
            INNER JOIN automatic_cashback_rule_rel ar ON ar.automatic_cashback_lines_id = acl.id 
            INNER JOIN cashback_rule_line crl ON crl.id = ar.cashback_rule_line_id 
            WHERE acl.date between '{0}' and '{1}' and acl.state = 'waiting_for_approval' 
            and crl.rule_id = {2} and mcc.group_id = {3} and crl.frequency = '{4}' 
            GROUP BY acl.id""".format(dfrom, dto, self.id, group_id, freq))
        rsc = cr.dictfetchall()
        if rsc:
            for rs in rsc:
                cr.execute("""DELETE FROM automatic_cashback_lines WHERE id = {0}""".format(rs['id']))
                cr.execute("""DELETE FROM automatic_cashback_rule_rel 
                    WHERE automatic_cashback_lines_id = {0}""".format(rs['id']))
        return cnt

    @api.model
    def cron_automate_cashback_in(self, frequency):
        cr = self.env.cr
        cid = self.company_id.id
        cr.execute("""SELECT mcc.id, mcc.group_id FROM master_customer_cashback mcc
            WHERE mcc.company_id = {0} and mcc.state='confirm' 
            order by mcc.group_id""".format(cid))
        res = cr.dictfetchall()
        if res:
            for rs in res:
                mcc_id = rs['id']
                group_id = rs['group_id']
                revenue, target, date, status = self.compute_revenue(group_id, cid, frequency)
                if frequency in ['annual','quarter','6month']:
                    total = 0.0
                    ref = ''
                    line_id = []
                    if target > 0:
                        for line in self.line_ids.filtered(lambda r: r.frequency==frequency).sorted(key=lambda r: r.sequence):
                            amount, details, lid = self.compute_cashback_in(line, group_id, frequency, revenue, target, status)
                            total = amount if amount > 0.0 else total
                            ref = details if amount > 0.0 else ref
                            line_id = lid if amount > 0.0 else line_id
                else:
                    data = []
                    for line in self.line_ids.filtered(lambda r: r.frequency=='month').sorted(key=lambda r: r.sequence):
                        data.append({
                            'id': line.id,
                            'name': line.name,
                            'trigger': line.trigger,
                            'sub_type': line.sub_type,
                            'formula': line.formula,
                            'target': line.sales_target,
                        })
                    x = 0
                    for i in data:
                        x += 1
                        if x < len(data):
                            value = data[x].get('target') if data[x].get('sub_type') == 'class' else 0.0
                        else:
                            value = 0.0
                        i.update({'range': value})
                    total, ref, line_id = self.compute_cashback_in(data, group_id, frequency, revenue, target, status)
                check = self.check_duplicated_cashback(frequency, group_id, date)
                if not check and total > 0.0:
                    self.env['automatic.cashback.lines'].create({
                        'reference': ref,
                        'cashback_id': mcc_id,
                        'date': date,
                        'user_id': 1,
                        'type_id': self.env.ref('adireksa_cashback_pattern.cashback_value_auto').id,
                        'value': total,
                        'state': 'waiting_for_approval',
                        'cashback_rule_id': [(6, 0, line_id)],
                    })


class CashbackRuleLine(models.Model):
    _name = 'cashback.rule.line'
    _description = 'Cashback Rule Line'

    name = fields.Char(string='Name')
    sequence = fields.Integer(string='Sequence', default=0)
    rule_id = fields.Many2one('cashback.rule', string='Cashback Rule', ondelete='cascade')
    state = fields.Selection([('draft','Draft'),('approve','Approved'),('cancel','Cancelled')], 
        string='Status', related='rule_id.state')
    trigger = fields.Selection([
        ('revenue', 'Hit Target Revenue'),
        ('sales', 'Hit Sales Target'),
        ('invoice', 'Pay Invoice'),
        ('promo', 'All or Selected products'),
    ], string='Trigger', default='revenue')
    frequency = fields.Selection([
        ('na', 'N/A'),
        ('month', 'Monthly'),
        ('quarter', 'Quarterly'),
        ('6month', '6 Month'),
    ], string='Frequency', default='na')
    sub_type = fields.Selection([
        ('na', 'N/A'),
        ('class', 'Class'),
        ('lunas', 'Pelunasan'),
        ('area1', 'Wilayah I'),
        ('area2', 'Wilayah II')
    ], string='Sub-type', default='na')
    target_modifier = fields.Float(string='Target Modifier', default=0.0)
    sales_target = fields.Float(string='Sales Target', default=0.0)
    day1 = fields.Integer(string='Day 1', default=0)
    day2 = fields.Integer(string='Day 2', default=0)
    product_ids = fields.Many2many('product.product', string='Products')
    formula = fields.Float(string='Formula (%)', default=0.0)
