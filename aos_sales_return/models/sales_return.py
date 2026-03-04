from odoo import models,fields,api,_
from odoo.exceptions import UserError

class SalesReturn(models.Model):
    _name = "sales.return"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = "Sales Return"
    _order = "id Desc"

    def _get_default_warehouse(self):
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1,order="id desc")

    def _get_default_customer_location(self):
        return self.env['stock.location'].search([('usage','=','customer')],limit=1)
    
    # def _get_receipt_location(self):
    #     return self._get_default_warehouse().lot_stock_id



    name = fields.Char(string="Number",default="New",readonly=True)
    partner_id = fields.Many2one('res.partner',string="Customer",tracking=True,required=True)
    document = fields.Char(string="Reference",)
    notes = fields.Text(string="Notes")
    date = fields.Date(string="Date",default=lambda self:fields.Date.today())
    state = fields.Selection([
                                ('draft','Draft'),
                                ('confirm','Confirm'),
                                ('incoming','Receipt'),
                                ('outgoing','Delivery'),
                                ('picking_create','Picking Created'),
                                ('done','Done'),
                                ('cancel','Cancel'),
                            ],string="State",default="draft",readonly=True,tracking=True)
    return_line_ids = fields.One2many('sales.return.line','return_id',string="Sales Return Line")
    receipt_picking_count = fields.Integer(string="Receipt Count",compute="_compute_picking_count")
    delivery_picking_count = fields.Integer(string="Delivery Count",compute="_compute_picking_count")
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",default=_get_default_warehouse)
    receipt_dest_location_id = fields.Many2one('stock.location',string="Receipt Destination Location",)
    receipt_source_location_id = fields.Many2one('stock.location',string="Receipt Source Location")
    delivery_dest_location_id = fields.Many2one('stock.location',string="Delivery Destination Location")
    delivery_source_location_id = fields.Many2one('stock.location',string="Delivery Source Location", )
    receipt_picking_type_id = fields.Many2one('stock.picking.type',string="Receipt To")
    delivery_picking_type_id = fields.Many2one('stock.picking.type',string="Delivery To")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id, track_visibility='onchange')
    currency_id = fields.Many2one('res.currency',string="Currency", default=lambda self:self.env.company.currency_id)
    create_picking = fields.Boolean(compute="_compute_action_to_transfer")
    is_picking_done = fields.Boolean(compute="_compute_picking_done")
    
    
    @api.model
    def default_get(self,fields):
        res = super(SalesReturn,self).default_get(fields)
        warehouse_id = self._get_default_warehouse()
        # Receipt
        if 'receipt_picking_type_id' not in res:
            res['receipt_picking_type_id'] = self.env['stock.picking.type'].search([('warehouse_id', '=', warehouse_id.id), ('is_return_in', '=', True)], limit=1).id
            picking_type = self.env['stock.picking.type'].browse( res['receipt_picking_type_id'] )
            
            res['receipt_dest_location_id'] = picking_type.default_location_dest_id.id
            res['receipt_source_location_id'] = picking_type.default_location_src_id.id or self._get_default_customer_location().id
        
        # Delivery
        if 'delivery_picking_type_id' not in res:
            res['delivery_picking_type_id'] = self.env['stock.picking.type'].search([('warehouse_id', '=', warehouse_id.id), ('is_return_out', '=', True)], limit=1).id
            picking_type = self.env['stock.picking.type'].browse( res['delivery_picking_type_id'] )
            
            res['delivery_dest_location_id'] = picking_type.default_location_dest_id.id or self._get_default_customer_location().id
            res['delivery_source_location_id'] = picking_type.default_location_src_id.id
        return res

    @api.onchange('warehouse_id')
    def _onchange_picking_type_location(self):
        if not self.warehouse_id:
            return
        return_in = self.env['stock.picking.type'].search([('warehouse_id', '=', self.warehouse_id.id), ('is_return_in', '=', True)], limit=1)
        return_out = self.env['stock.picking.type'].search([('warehouse_id', '=', self.warehouse_id.id), ('is_return_out', '=', True)], limit=1)
        
        customer_location_id = self._get_default_customer_location().id
        
        # Receipt
        self.receipt_picking_type_id = return_in.id
        self.receipt_source_location_id = self.receipt_picking_type_id.default_location_src_id.id or customer_location_id
        self.receipt_dest_location_id = self.receipt_picking_type_id.default_location_dest_id.id
        
        # Delivery
        self.delivery_picking_type_id = return_out.id
        self.delivery_source_location_id = self.delivery_picking_type_id.default_location_src_id.id
        self.delivery_dest_location_id = self.delivery_picking_type_id.default_location_dest_id.id or customer_location_id
        
        
    @api.onchange('receipt_picking_type_id')
    def onchange_picking_type_receipt(self):
        if not self.receipt_picking_type_id: return
        
        customer_location_id = self._get_default_customer_location().id
        self.receipt_source_location_id = self.receipt_picking_type_id.default_location_src_id.id or customer_location_id
        self.receipt_dest_location_id = self.receipt_picking_type_id.default_location_dest_id.id
        
    @api.onchange('delivery_picking_type_id')
    def onchange_picking_type_delivery(self):
        if not self.delivery_picking_type_id: return
        
        customer_location_id = self._get_default_customer_location().id
        self.delivery_source_location_id = self.delivery_picking_type_id.default_location_src_id.id
        self.delivery_dest_location_id = self.delivery_picking_type_id.default_location_dest_id.id or customer_location_id
        
    def unlink(self):
        for sr in self:
            if sr.state not in ('draft', 'cancel'):
                raise UserError(_('Cannot delete Sales Return other than draft and cancel'))
        return super(SalesReturn, self).unlink()

    def _compute_picking_count(self):
        for rec in self:
            lines = self._get_filtered_line()
            pickings = self._get_picking_list(lines)
            rec.delivery_picking_count = len(pickings[0])
            rec.receipt_picking_count = len(pickings[1])

    @api.depends(
                    'return_line_ids.delivery_moves_ids.picking_id.state',
                    'return_line_ids.receipt_moves_ids.picking_id.state',
            )
    def _compute_action_to_transfer(self):
        for rec in self:
            rec.create_picking = False
            
            if not any(rec.return_line_ids.delivery_moves_ids.picking_id.filtered(lambda p: p.state in ('done','confirmed','assigned','draft'))):
                rec.create_picking = True
            
            if not any(rec.return_line_ids.receipt_moves_ids.picking_id.filtered(lambda p: p.state in ('done','confirmed','assigned','draft'))):
                rec.create_picking = True

    @api.depends(
            'return_line_ids.receipt_moves_ids.picking_id.state',
            'return_line_ids.delivery_moves_ids.picking_id.state',
    )
    def _compute_picking_done(self):
        for rec in self:
            rec.is_picking_done = rec.return_line_ids.receipt_moves_ids.picking_id.filtered(lambda p:p.state == 'done') and \
                                    rec.return_line_ids.delivery_moves_ids.picking_id.filtered(lambda p:p.state == 'done') and \
                                        rec.state != 'done'
            
    def _validate_replacement_line(self):
        if not self.return_line_ids:
            raise UserError(_("Return line is required for receipt or delivery"))
        lines = self.return_line_ids.filtered(lambda x:x.replacement_action_type_id.is_replacement and not x.replacement_product_ids)
        if lines:
            raise UserError(_("Some return line use replacement type and doesn't have product replacement"))

    def action_confirm(self):
        self._validate_replacement_line()
        self.state = "confirm"
    
    def action_draft(self):
        self.state = "draft"
    
    def action_done(self):
        # JIKA ACTION DONE SAMA DENGAN STATUS DONE STOCK PICKING MAKA ACTION DONE BISA DI KLIK 
        self._validate_replacement_line()
        lines = self._get_filtered_line()
        self.state = "done"


    def action_cancel(self):
        pickings = self._get_picking_list(self.return_line_ids)
        (pickings[0] + pickings[1]).filtered(lambda p: p.state != 'done').action_cancel()
        self.state = "cancel"
        
    def _get_filtered_line(self):
        return self.return_line_ids.filtered(lambda x:x.action_type_id.is_receipt or x.replacement_product_ids)

    def action_view_picking(self):
        type_code = self.env.context.get('picking_type','incoming')
        lines = self._get_filtered_line()
        pickings = self._get_picking_list(lines)
        if type_code == 'outgoing':
            pickings = pickings[0]
        else:
            pickings = pickings[1]
        return {
                'name':_("Sales Return Transfer %s" %(self.name)),
                'type':'ir.actions.act_window',
                'res_model':'stock.picking',
                'view_mode':'tree,form',
                'domain':[('id','in',pickings.ids)],
        }

    @api.model
    def _get_picking_list(self,lines):
        """
            Return list[stock.picking]: [picking_delivery, picking_receipt]
        """
        delivery_picking = lines.delivery_moves_ids.picking_id
        receipt_picking = lines.receipt_moves_ids.picking_id
        return [delivery_picking, receipt_picking]
        
    def _get_prepare_picking(self):
        type_code = self._context.get('picking_type','incoming')
        company_id = self.company_id.id or self.env.context.get('company_id',self.env.company.id)
        warehouse = self.warehouse_id or self._get_default_warehouse()

        if type_code == 'incoming':
            location = {'location_dest_id':self.receipt_dest_location_id.id, 'location_id':self.receipt_source_location_id.id}
            picking_type = self.receipt_picking_type_id

        if type_code == 'outgoing':
            location = {'location_id':self.delivery_source_location_id.id, 'location_dest_id':self.delivery_dest_location_id.id}
            picking_type = self.delivery_picking_type_id

        vals = {
                'partner_id':self.partner_id.id,
                'scheduled_date':self.date,
                'picking_type_id':picking_type.id,
                'origin':self.name,
                'sales_return_id':self.id,
            }
        vals.update(location)
        return vals
    
    
    def _prepare_stock_move(self,return_line,picking):
        result = []
        type_code = self.env.context.get('picking_type','incoming')
        company = self.env.context.get('company_id') or self.company_id or self.env.company
        for line in return_line:
            vals = {'product_id':line.product_id.id,
                    'product_uom_qty':line.qty,
                    'product_uom':line.product_id.uom_id.id,
                    'date':line.return_id.date,
                    'company_id':company.id,
                    'origin':f"Sales Return {line.return_id.name} {type_code.capitalize()}/{line.product_id.default_code or ''}",
                    'name':f"Sales Return {type_code.capitalize()}/{line.product_id.default_code or ''}",
                    type_code + '_sales_return_line_id':line.id,
                    'picking_id':picking.id,
                    'location_dest_id':picking.location_dest_id.id, 
                    'location_id':picking.location_id.id,
                }
            if line.replacement_product_ids and type_code != 'incoming':
                for replacement in line.replacement_product_ids:
                    replacement_vals = vals.copy()
                    replacement_vals['product_id'] = replacement.product_id.id
                    replacement_vals['product_uom_qty'] = replacement.qty
                    replacement_vals['product_uom'] = replacement.product_id.uom_id.id
                    result.append(replacement_vals)
                continue
            result.append(vals)
        return result

    def _create_picking(self):
        lines = self._get_filtered_line()
        vals = self._get_prepare_picking()
        picking = self.env['stock.picking'].create(vals)
        vals_moves = self._prepare_stock_move(lines,picking)
        self.env['stock.move'].create(vals_moves)
        return picking

    def action_create_picking(self):
        type_code = self.env.context.get('picking_type','incoming')
        # if type_code == 'outgoing':
        #     self._validate_replacement_line()
        # lines = self._get_filtered_line()
        # Selected line jika tidak ada moves atau moves dengan status cancel
        Picking = self.env['stock.picking']
        pickings = self._get_picking_list(self.return_line_ids)
        # Delivery Picking
        create_delivery = not any(pickings[0].filtered(lambda p: p.state in ('done','confirmed','assigned','draft')))
        if create_delivery:
            return_do = self.with_context({},picking_type="outgoing")
            Picking += return_do._create_picking()
            
        
        # Receipt Picking
        create_receipt = not any(pickings[1].filtered(lambda p: p.state in ('done','confirmed','assigned','draft')))
        if create_receipt:
            return_receipt = self.with_context({},picking_type="incoming")
            Picking += return_receipt._create_picking()
        Picking.action_confirm()
        if self.state == 'confirm':
            self.state = 'picking_create'
    
    @api.model
    def create(self,vals):
        # if not vals.get('return_line_ids'):
        #     raise UserError("Please Define Return Line")
        if vals.get('name',"New") == "New":
            sequence = self.env['ir.sequence'].next_by_code('sales.return')
            vals['name'] = sequence
        return super(SalesReturn,self).create(vals)
    