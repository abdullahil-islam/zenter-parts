# wizard/travel_advance_payment_wizard.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from markupsafe import Markup


class TravelAdvancePaymentWizard(models.TransientModel):
    _name = 'travel.advance.payment.wizard'
    _description = 'Make Advance Payment for Travel'

    travel_id = fields.Many2one('corporate.travel', string='Travel Request', required=True)
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 domain="[('type','in',('bank','cash'))]")
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')
    partner_id = fields.Many2one('res.partner', string='Partner', required=False)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    memo = fields.Char(string='Memo')

    @api.model
    def default_get(self, fields_list):
        res = super(TravelAdvancePaymentWizard, self).default_get(fields_list)
        active_travel = self.env.context.get('default_travel_id') or self.env.context.get('active_id')
        if active_travel:
            travel = self.env['corporate.travel'].browse(active_travel)
            res.update({
                'travel_id': travel.id,
                'currency_id': travel.currency_id.id if travel.currency_id else self.env.company.currency_id.id,
                'partner_id': travel.employee_id.user_id.partner_id.id if travel.employee_id and travel.employee_id.user_id.partner_id else travel.employee_id.work_contact_id.id if travel.employee_id and travel.employee_id.work_contact_id else False,
            })
        return res

    def action_create_payment(self):
        self.ensure_one()

        # Validations
        if not self.journal_id:
            raise UserError(_('Please select a journal.'))
        if self.amount <= 0:
            raise UserError(_('Amount must be positive.'))
        if not self.account_id:
            raise UserError(_('Please select an account.'))
        if not self.partner_id:
            raise UserError(_('Partner is required to create vendor bill.'))

        try:
            # Step 1: Create Vendor Bill
            bill_vals = {
                'move_type': 'in_invoice',
                'partner_id': self.partner_id.id,
                'invoice_date': self.payment_date,
                'date': self.payment_date,
                'currency_id': self.currency_id.id,
                'ref': _('Travel Advance - %s') % (self.travel_id.name or self.travel_id.display_name),
                'invoice_line_ids': [(0, 0, {
                    'product_id': False,
                    'account_id': self.account_id.id,
                    'quantity': 1,
                    'price_unit': self.amount,
                    'name': self.memo or _('Travel Advance Payment for %s') % (self.travel_id.display_name),
                })],
            }

            Bill = self.env['account.move'].sudo()
            bill = Bill.create(bill_vals)

            # Post the vendor bill
            bill.action_post()

            # Step 2: Create Payment
            payment_vals = {
                'payment_type': 'outbound',
                'amount': self.amount,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'partner_id': self.partner_id.id,
                'partner_type': 'supplier',
                'currency_id': self.currency_id.id,
                'memo': self.memo or _('Advance payment for travel %s') % (self.travel_id.display_name),
            }

            Payment = self.env['account.payment'].sudo()
            payment = Payment.create(payment_vals)

            # Post the payment (this should auto-reconcile with the bill)
            payment.action_post()

            # Step 3: Manual Reconciliation
            # Find the payable line from the bill
            bill_payable_line = bill.line_ids.filtered(
                lambda l: l.account_id.account_type == 'liability_payable' and not l.reconciled
            )

            # Find the liquidity line from the payment
            payment_liquidity_line = payment.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'liability_payable' and not l.reconciled
            )

            if bill_payable_line and payment_liquidity_line:
                # Reconcile the lines
                lines_to_reconcile = bill_payable_line | payment_liquidity_line
                lines_to_reconcile.reconcile()
            else:
                raise UserError(_('Could not find lines to reconcile. Bill payable: %s, Payment payable: %s') % (
                    bool(bill_payable_line), bool(payment_liquidity_line)
                ))

            # Step 4: Link to travel record
            self.travel_id.sudo().write({
                'advance_payment_id': payment.id,
                'advance_move_id': bill.id,
                'advance_account_id': self.account_id.id,
                'advance_amount': self.amount,
                'advance_state': 'paid',
            })

            # Post chatter message with bill and payment references
            self.travel_id.message_post(
                body=Markup(('Travel advance processed:<br/>- Vendor Bill: <span class="text-info">%s</span><br/>- Payment: <span class="text-info">%s</span><br/>- Amount: <span class="text-info">%s</span> %s') % (
                    bill.name,
                    payment.name,
                    self.amount,
                    self.currency_id.symbol or self.currency_id.name
                ))
            )

            return {'type': 'ir.actions.act_window_close'}

        except Exception as e:
            # Rollback will happen automatically due to transaction management
            raise UserError(_('Failed to create vendor bill and payment: %s') % str(e))
