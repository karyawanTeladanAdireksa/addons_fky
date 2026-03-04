# from random import randint
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    split_bool = fields.Boolean(compute="_compute_split")
    keterangan = fields.Text(string="Reference")


    def button_validate(self):
        if 0 in self.cost_lines.mapped('price_unit'):
            raise UserError(_('Cost can not be 0, You Should maybe recompute the Landed Cost'))
        return super(StockLandedCost,self).button_validate()
    
    def button_create_bm(self):
        form = self.env.ref('aos_landed_cost_bm.vendor_bill_wizard_form_view')
        context = dict(self.env.context or {})
        context.update({'active_id':self.id,
                        'active_model':self._name,
                        'default_cost_id':self.id,
                        'default_cost_lines':[(6, False, [self.cost_lines.ids])]
                        })
        res = {
            'name': "Create Vendor Bill",
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vendor.bill.wizard',
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }
        return res

    def check_line_bm(self,vals):
        self = self or vals
        if len(self.cost_lines) >=2 :
            if 'by_bm' in self.cost_lines.mapped('split_method') :
                raise UserError(_('Split Method Tidak Bisa Digabung Dengan Method Lain'))

    @api.model
    def create(self,vals):
        res = super(StockLandedCost,self).create(vals)
        self.check_line_bm(res)
        return res
    
    def write(self,vals):
        res = super(StockLandedCost,self).write(vals)
        self.check_line_bm(vals)
        return res


    def _compute_split(self):
        for rec in self:
            rec.split_bool = False
            if len(rec.cost_lines) == 1 :
                if rec.cost_lines.split_method == 'by_bm':
                    rec.split_bool = True

    
    def get_valuation_bm_lines(self):
        self.ensure_one()
        lines = []

        for move in self._get_targeted_move_ids():
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel' or not move.product_qty:
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.stock_valuation_layer_ids[0].value,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines:
            target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
            raise UserError(_("You cannot apply landed costs on the chosen %s(s). Landed costs can only be applied for products with FIFO or average costing method.", target_model_descriptions[self.target_model]))
        return lines
    
    def compute_landed_cost(self):
        if len(self.cost_lines) == 1:
            if self.cost_lines.split_method == 'by_bm':
                return
        return super(StockLandedCost,self).compute_landed_cost()
        


    def compute_landed_cost_bm(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
            rounding = cost.currency_id.rounding
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_bm_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += cost.currency_id.round(former_cost)

                total_line += 1
            price_unit = 0 
            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        value = valuation.former_cost * valuation.bea_masuk // 100
                        price_unit += value
                        if rounding:
                            value = tools.float_round(value, precision_rounding=rounding, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
            line.write({'price_unit':price_unit})
        for key, value in towrite_dict.items():
            adjusment = AdjustementLines.browse(key)
            adjusment.write({'additional_landed_cost': value,'final_cost':adjusment.former_cost + value})
        return True


class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'
    qty = fields.Integer(string="Qty",default="1")
    split_method = fields.Selection(
        selection_add=[
            ("by_bm", "By Bea Masuk"),
        ],
        ondelete={"by_bm": "cascade"},
    )

    @api.onchange("split_method")
    def _onchange_split_method(self):
        if self.split_method == 'by_bm':
            self.write({'price_unit':0})

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.name = self.product_id.name or ''
        self.split_method = self.product_id.product_tmpl_id.split_method_landed_cost or self.split_method or 'equal'
        self.price_unit = self.product_id.standard_price or 0.0
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        self.account_id = self.product_id.landed_account.id

    def write(self,vals):
        if vals.get('split_method'):
            self.cost_id.valuation_adjustment_lines = False
        return super(StockLandedCostLine,self).write(vals)

    

class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    bea_masuk = fields.Integer(string="Bea Masuk (%)",related="product_id.bea_masuk")

   
