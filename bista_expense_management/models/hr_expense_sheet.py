from odoo import models, fields, api, _


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    # Add reverse relationship to corporate.travel
    travel_id = fields.Many2one('corporate.travel', string='Travel Request', readonly=True, copy=False)

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

            # Recompute the totals
            # bill._recompute_dynamic_lines(recompute_all_taxes=True)

            # Update advance balance
            # new_balance = advance_amount - calculated_amount
            # sheet.travel_id.sudo().write({
            #     'advance_balance': new_balance,
            # })

            # If advance is fully consumed, update state to reconciled
            # if new_balance <= 0:
            #     # sheet.travel_id.sudo().write({
            #     #     'advance_state': 'reconciled',
            #     # })
            #
            #     # Post message to travel record
            #     sheet.travel_id.message_post(
            #         body=_('Travel advance fully reconciled with expense sheet: %s') % sheet.name
            #     )
            # else:
            #     # Post message about partial reconciliation
            #     sheet.travel_id.message_post(
            #         body=_('Travel advance partially reconciled. Amount: %s, Remaining balance: %s') % (
            #             calculated_amount, new_balance
            #         )
            #     )

        return moves
