from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    travel_id = fields.Many2one(
        'corporate.travel', 
        string='Travel Request', 
        readonly=True, 
        copy=False,
        help="Link to the travel request that created this PO"
    )
    is_travel_po = fields.Boolean(
        string='Is Travel PO',
        compute='_compute_is_travel_po',
        store=True,
        help="Indicates if this PO is linked to a travel request"
    )
    po_fully_paid = fields.Boolean(
        string='Fully Paid',
        compute='_compute_po_fully_paid',
        store=True,
        help="True when all bills for this PO are fully paid"
    )

    @api.depends('travel_id')
    def _compute_is_travel_po(self):
        for po in self:
            po.is_travel_po = bool(po.travel_id)

    @api.depends('invoice_ids', 'invoice_ids.payment_state', 'invoice_ids.state')
    def _compute_po_fully_paid(self):
        """Check if all bills related to this PO are fully paid"""
        for po in self:
            if not po.invoice_ids:
                po.po_fully_paid = False
                continue
            
            # Check if all posted bills are paid
            posted_bills = po.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            if not posted_bills:
                po.po_fully_paid = False
                continue
            
            # All bills must be in 'paid' payment state
            all_paid = all(bill.payment_state == 'paid' for bill in posted_bills)
            po.po_fully_paid = all_paid

    def _update_expense_sheet_on_payment(self):
        """Update linked expense sheet when PO is fully paid"""
        for po in self:
            if not po.travel_id or not po.po_fully_paid:
                continue
            
            # Find the PO expense sheet
            po_expense_sheet = po.travel_id.expense_sheet_ids.filtered(
                lambda sheet: 'PO Expenses' in sheet.name
            )
            
            if po_expense_sheet and po_expense_sheet.state != 'done':
                # Check if ALL POs for this travel are fully paid
                all_travel_pos = po.travel_id.purchase_order_ids
                all_pos_paid = all(p.po_fully_paid for p in all_travel_pos)
                
                if all_pos_paid:
                    try:
                        # Mark expense sheet as done/paid
                        if hasattr(po_expense_sheet, 'action_sheet_move_create'):
                            # If not already posted, post it first
                            if po_expense_sheet.state == 'approve':
                                po_expense_sheet.action_sheet_move_create()
                        
                        # Set to done
                        po_expense_sheet.write({'state': 'done'})
                        
                        # Post message
                        po.travel_id.message_post(
                            body=_('PO Expense Sheet marked as paid - all Purchase Orders are fully paid')
                        )
                    except Exception as e:
                        # Log but don't block
                        po.travel_id.message_post(
                            body=_('Note: Could not auto-update expense sheet status: %s') % str(e)
                        )


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    travel_line_id = fields.Many2one(
        'corporate.travel.line',
        string='Travel Line',
        readonly=True,
        copy=False,
        help="Link to the travel request line that created this PO line"
    )
    is_travel_line = fields.Boolean(
        string='Is Travel Line',
        compute='_compute_is_travel_line',
        store=True,
        help="Indicates if this PO line is linked to a travel request"
    )

    @api.depends('travel_line_id')
    def _compute_is_travel_line(self):
        for line in self:
            line.is_travel_line = bool(line.travel_line_id)

    def write(self, vals):
        """Prevent modifications to PO lines linked to travel requests"""
        for line in self:
            if line.travel_line_id:
                # Define which fields are protected
                protected_fields = {
                    'product_id', 'product_qty', 'price_unit', 
                    'name', 'product_uom'
                }
                
                # Check if any protected field is being modified
                modified_protected = protected_fields & set(vals.keys())
                
                if modified_protected:
                    raise UserError(_(
                        'Cannot modify Purchase Order line "%s".\n\n'
                        'This line is linked to Travel Request: %s\n'
                        'Protected fields: %s\n\n'
                        'Please modify the travel request instead or unlink it from the travel request first.'
                    ) % (
                        line.name or line.product_id.name,
                        line.order_id.travel_id.name if line.order_id.travel_id else 'Unknown',
                        ', '.join(modified_protected)
                    ))
        
        return super(PurchaseOrderLine, self).write(vals)

    def unlink(self):
        """Prevent deletion of PO lines linked to travel requests"""
        for line in self:
            if line.travel_line_id:
                raise UserError(_(
                    'Cannot delete Purchase Order line "%s".\n\n'
                    'This line is linked to Travel Request: %s\n\n'
                    'Travel-linked PO lines cannot be deleted to maintain traceability.'
                ) % (
                    line.name or line.product_id.name,
                    line.order_id.travel_id.name if line.order_id.travel_id else 'Unknown'
                ))
        
        return super(PurchaseOrderLine, self).unlink()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _write(self, vals):
        """Monitor payment state changes to trigger expense sheet updates"""
        result = super(AccountMove, self)._write(vals)
        
        # If payment_state changed to 'paid', check for linked travel POs
        if 'payment_state' in vals and vals.get('payment_state') == 'paid':
            for move in self:
                if move.move_type == 'in_invoice':  # Vendor bill
                    # Find related POs
                    related_pos = move.line_ids.mapped('purchase_line_id.order_id').filtered(
                        lambda po: po.travel_id
                    )
                    
                    if related_pos:
                        # Trigger recomputation and expense sheet update
                        related_pos._compute_po_fully_paid()
                        related_pos._update_expense_sheet_on_payment()
        
        return result