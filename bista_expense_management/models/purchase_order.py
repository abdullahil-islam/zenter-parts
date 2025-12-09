from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


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
            all_paid = all(bill.payment_state == 'paid' or bill.payment_state == 'in_payment' for bill in posted_bills)
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
                        # Set to done
                        po_expense_sheet.approval_state = 'submit'

                        # Post message
                        po.travel_id.message_post(
                            body=_('PO Expense Sheet marked as paid - all Purchase Orders are fully paid')
                        )
                    except Exception as e:
                        # Log but don't block
                        po.travel_id.message_post(
                            body=_('Note: Could not auto-update expense sheet status: %s') % str(e)
                        )

    def action_create_invoice(self):
        res = super().action_create_invoice()
        for order in self:
            if order.is_travel_po and order.travel_id and order.travel_id.state == 'approved':
                po_expense_sheet = order.travel_id.expense_sheet_ids.filtered(
                    lambda sheet: 'PO Expenses' in sheet.name
                )
                if po_expense_sheet:
                    for move in order.invoice_ids.filtered(lambda m: m.state == 'draft'):
                        move.po_expense_sheet_id = po_expense_sheet.id
        return res


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
        """Sync PO line changes to corresponding expense lines"""
        for line in self:
            if line.travel_line_id:
                # Define which fields are protected
                protected_fields = {
                    'product_id', 'product_uom'
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

        # Call parent write first
        result = super(PurchaseOrderLine, self).write(vals)

        # Fields that trigger sync to expense
        sync_fields = {'price_unit', 'product_qty', 'name'}

        # Check if any sync field was modified
        if sync_fields & set(vals.keys()):
            for line in self:
                if line.travel_line_id:
                    line._sync_to_expense_line(vals)

        return result

    def _sync_to_expense_line(self, changed_vals):
        """Sync PO line changes to the corresponding expense line"""
        self.ensure_one()

        if not self.travel_line_id:
            return

        # Find the expense line linked to this travel line
        expense_line = self.env['hr.expense'].search([
            ('travel_line_id', '=', self.travel_line_id.id)
        ], limit=1)

        if not expense_line:
            return

        # Prepare values to update in expense
        expense_vals = {}

        # Sync price: PO line price_unit → Expense total_amount_currency
        if 'price_unit' in changed_vals or 'product_qty' in changed_vals:
            # Calculate new total: price_unit * quantity
            new_total = self.price_unit * self.product_qty
            expense_vals['total_amount_currency'] = new_total

        # Sync product
        # if 'product_id' in changed_vals:
        #     product = self.env['product.template'].browse(changed_vals['product_id'])
        #     expense_vals['product_id'] = self.product_id.id

        # Sync description/name
        if 'name' in changed_vals:
            expense_vals['name'] = self.name

        # Update the expense line
        if expense_vals:
            try:
                expense_line.sudo().write(expense_vals)

                # Post message to travel request
                if self.order_id.travel_id:
                    self.order_id.travel_id.message_post(
                        body=_('PO line updated and synced to expense: %s (New amount: %s)') % (
                            self.name or self.product_id.name,
                            new_total if 'price_unit' in changed_vals or 'product_qty' in changed_vals else 'N/A'
                        )
                    )
            except Exception as e:
                # Log error but don't block PO update
                _logger.warning(f"Failed to sync PO line to expense: {str(e)}")

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

    is_expenses_updated = fields.Boolean(default=False)
    po_expense_sheet_id = fields.Many2one(comodel_name='hr.expense.sheet', ondelete='set null', copy=False, index='btree_not_null')

    def write(self, vals):
        """Monitor payment state changes to trigger expense sheet updates"""
        result = super(AccountMove, self).write(vals)
        # If payment_state changed to 'paid', check for linked travel POs
        # if 'payment_state' in vals and vals.get('payment_state') in ['paid', 'in_payment']:
        for move in self:
            if move.move_type == 'in_invoice' and not self.is_expenses_updated and self.payment_state in ['paid', 'in_payment']:  # Vendor bill
                # Find related POs
                related_pos = move.line_ids.mapped('purchase_line_id.order_id').filtered(
                    lambda po: po.travel_id
                )

                if related_pos:
                    # Trigger recomputation and expense sheet update
                    related_pos._compute_po_fully_paid()
                    related_pos._update_expense_sheet_on_payment()
                    move.is_expenses_updated = True
        
        return result
