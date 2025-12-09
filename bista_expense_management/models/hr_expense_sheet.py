from odoo import models, fields, api, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    travel_line_id = fields.Many2one(
        'corporate.travel.line',
        string='Travel Line',
        readonly=True,
        copy=False,
        help="Link to the travel request line that created this expense"
    )


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    # Add reverse relationship to corporate.travel
    travel_id = fields.Many2one('corporate.travel', string='Travel Request', readonly=True, copy=False)
    po_account_move_ids = fields.One2many(
        string="Journal Entries",
        comodel_name='account.move', inverse_name='po_expense_sheet_id', readonly=True,
    )

    @api.depends('account_move_ids.payment_state', 'account_move_ids.amount_residual', 'po_account_move_ids.payment_state', 'po_account_move_ids.amount_residual')
    def _compute_from_account_move_ids(self):
        res = super()._compute_from_account_move_ids()
        for sheet in self:
            purchase_ids = self.po_account_move_ids.invoice_line_ids.mapped('purchase_order_id')
            if purchase_ids and 'PO Expenses' in sheet.name:
                sheet.amount_residual = sum(sheet.po_account_move_ids.mapped('amount_residual'))
                payment_states = set(sheet.po_account_move_ids.mapped('payment_state'))
                if len(payment_states) <= 1:  # If only 1 move or only one state
                    sheet.payment_state = payment_states.pop() if payment_states else 'not_paid'
                elif 'partial' in payment_states or 'paid' in payment_states:  # else if any are (partially) paid
                    sheet.payment_state = 'partial'
                else:
                    sheet.payment_state = 'not_paid'
                # if sheet.payment_state in ['paid', 'in_payment']:
                #     sheet.approval_state = 'submit'
        return res

    @api.depends('account_move_ids', 'po_account_move_ids', 'payment_state', 'approval_state')
    def _compute_state(self):
        for sheet in self:
            move_ids = sheet.account_move_ids | sheet.po_account_move_ids
            if not sheet.approval_state:
                sheet.state = 'draft'
            elif sheet.approval_state == 'cancel':
                sheet.state = 'cancel'
            elif move_ids:
                if sheet.payment_state != 'not_paid':
                    sheet.state = 'done'
                elif all(move_ids.mapped(lambda move: move.state == 'draft')):
                    sheet.state = 'approve'
                else:
                    sheet.state = 'post'
            else:
                sheet.state = sheet.approval_state  # Submit & approved without a move case

    def _do_create_moves(self):
        """
        Inherit the method to add advance adjustment line to 'Other Expenses' sheet bills
        """
        # Call the parent method to create the moves
        moves = super(HrExpenseSheet, self)._do_create_moves()

        # Process each expense sheet
        for sheet in self:
            # Check if this sheet is linked to a travel request
            if not sheet.travel_id:
                continue

            # Check if this is the "Other Expenses" sheet
            if not sheet.name or 'Other Expenses' not in sheet.name:
                continue

            # Check if there's an advance payment
            if not sheet.travel_id.advance_amount or sheet.travel_id.advance_amount <= 0:
                continue

            # Check if advance account is set
            if not sheet.travel_id.advance_account_id:
                continue

            # Check if payment mode is 'own_account' (employee to be reimbursed)
            if sheet.payment_mode != 'own_account':
                continue

            # Calculate the adjustment amount
            advance_amount = sheet.travel_id.advance_amount
            calculated_amount = min(advance_amount, sheet.total_amount)

            if calculated_amount <= 0:
                continue

            # Find the bill/move created for this sheet
            bill = False
            for move in moves:
                if move.id in sheet.account_move_ids.ids:
                    bill = move
                    break

            if not bill:
                continue

            # Add the advance adjustment line to the bill
            adjustment_line_vals = {
                'move_id': bill.id,
                'product_id': False,
                'account_id': sheet.travel_id.advance_account_id.id,
                'quantity': 1,
                'price_unit': -calculated_amount,  # Negative to reduce the payable amount
                'name': _('Travel Advance Adjustment - %s') % sheet.travel_id.name,
            }

            # Create the line
            self.env['account.move.line'].sudo().create(adjustment_line_vals)

        return moves
