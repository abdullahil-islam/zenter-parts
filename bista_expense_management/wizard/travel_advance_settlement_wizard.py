# wizard/travel_advance_settlement_wizard.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TravelAdvanceSettlementWizard(models.TransientModel):
    _name = 'travel.advance.settlement.wizard'
    _description = 'Settle Travel Advance Balance'

    travel_id = fields.Many2one('corporate.travel', string='Travel Request', required=True, readonly=True)
    balance_amount = fields.Monetary(string='Balance Amount', required=True, readonly=True, currency_field='currency_id')
    balance_type = fields.Selection([
        ('employee_owes', 'Employee Owes Company'),
        ('company_owes', 'Company Owes Employee')
    ], string='Balance Type', required=True, readonly=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 domain="[('type','in',('bank','cash'))]")
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    memo = fields.Char(string='Memo')
    
    # Display fields for context
    advance_amount = fields.Monetary(string='Original Advance', related='travel_id.advance_amount', readonly=True)
    actual_expense = fields.Monetary(string='Actual Expenses', related='travel_id.actual_other_expense', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        travel_id = self.env.context.get('default_travel_id')
        
        if travel_id:
            travel = self.env['corporate.travel'].browse(travel_id)
            partner = travel.employee_id.user_id.partner_id or travel.employee_id.work_contact_id
            
            res.update({
                'travel_id': travel.id,
                'currency_id': travel.currency_id.id or self.env.company.currency_id.id,
                'partner_id': partner.id if partner else False,
                'memo': _('Settlement for travel %s') % travel.name,
            })
        
        return res

    def action_create_settlement_payment(self):
        """Create payment to settle the advance balance"""
        self.ensure_one()

        if self.travel_id.settlement_payment_id:
            raise UserError(_('This Request is already settled once.'))
        
        if not self.journal_id:
            raise UserError(_('Please select a journal.'))
        
        if self.balance_amount <= 0:
            raise UserError(_('Balance amount must be positive.'))
        
        # Determine payment type and partner type
        if self.balance_type == 'employee_owes':
            # Employee returns money to company -> Inbound payment
            payment_type = 'inbound'
            partner_type = 'supplier'
            memo = self.memo or _('Return of excess advance for travel %s') % self.travel_id.name
        else:
            # Company pays remaining to employee -> Outbound payment
            payment_type = 'outbound'
            partner_type = 'supplier'
            memo = self.memo or _('Additional payment for travel %s') % self.travel_id.name
        
        payment_vals = {
            'payment_type': payment_type,
            'partner_type': partner_type,
            'amount': self.balance_amount,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'currency_id': self.currency_id.id,
            'payment_reference': self.travel_id.name,
            'memo': memo,
        }
        
        Payment = self.env['account.payment'].sudo()
        payment = Payment.create(payment_vals)
        
        # Post the payment
        try:
            payment.action_post()
        except AttributeError:
            try:
                payment.post()
            except Exception:
                pass  # Leave in draft if posting fails
        
        # Update travel record
        new_state = 'fully_settled' if abs(self.travel_id.advance_balance) - self.balance_amount < 0.01 else 'partially_settled'
        
        self.travel_id.sudo().write({
            'settlement_payment_id': payment.id,
            'advance_state': new_state,
        })
        
        # Post message to chatter
        if self.balance_type == 'employee_owes':
            message = _('Settlement payment created: Employee returned %s (Payment: %s)') % (
                self.balance_amount, payment.name or payment.id
            )
        else:
            message = _('Settlement payment created: Additional payment of %s to employee (Payment: %s)') % (
                self.balance_amount, payment.name or payment.id
            )
        
        self.travel_id.message_post(body=message)
        
        # Show success message and close
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Settlement payment created successfully!'),
                'type': 'success',
                'sticky': False,
            }
        }
