# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    backorder_qty = fields.Float(
        string='Backorder Qty',
        compute='_compute_backorder_qty',
        store=True,
        digits='Product Unit of Measure',
        help='Quantity remaining in backorder deliveries'
    )
    can_edit_discount = fields.Boolean(related='order_id.can_edit_discount')

    # def _compute_can_edit_discount(self):
    #     for rec in self:
    #         allowed_groups = ['bista_expense_management.group_md', 'bista_expense_management.group_fd', 'base.group_system', ]
    #         rec.can_edit_discount = any(self.env.user.has_group(group) for group in allowed_groups)
    #         # rec.can_edit_discount = False

    @api.depends('move_ids', 'move_ids.state', 'move_ids.product_uom_qty', 
                 'move_ids.picking_id', 'move_ids.picking_id.backorder_id',
                 'move_ids.picking_id.state', 'move_ids.picking_id.picking_type_id')
    def _compute_backorder_qty(self):
        """
        Compute the backordered quantity for each sale order line.
        
        Logic:
        - Find all stock moves linked to this sale order line
        - Filter for moves in backorder pickings (picking.backorder_id is set)
        - Filter for outgoing deliveries only
        - Filter for moves not in 'done' or 'cancel' state
        - Sum the product_uom_qty of these moves
        """
        for line in self:
            backorder_qty = 0.0
            
            if line.move_ids:
                # Filter stock moves for backordered quantities
                backorder_moves = line.move_ids.filtered(
                    lambda m: (
                        # The picking must be a backorder (has a backorder_id)
                        m.picking_id.backorder_id and
                        # Only count moves that are not done or cancelled
                        m.state not in ('done', 'cancel') and
                        # Only count outgoing deliveries
                        m.picking_id.picking_type_id.code == 'outgoing'
                    )
                )
                
                # Sum the quantities
                for move in backorder_moves:
                    # Convert to sale order line UOM if necessary
                    backorder_qty += move.product_uom._compute_quantity(
                        move.product_uom_qty,
                        line.product_uom,
                        rounding_method='HALF-UP'
                    )
            
            line.backorder_qty = backorder_qty
