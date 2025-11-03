# wizard/travel_advance_payment_wizard.py
from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
    memo = fields.Char(string='Memo')
    # available_partner_id = fields.Many2many('res.partner', compute='')

    # available_journal_ids = fields.Many2many(
    #     comodel_name='account.journal',
    #     compute='_compute_available_journal_ids'
    # )
    #
    # def _compute_available_journal_ids(self):
    #     for rec in self:
    #         pass

    @api.model
    def default_get(self, fields_list):
        res = super(TravelAdvancePaymentWizard, self).default_get(fields_list)
        active_travel = self.env.context.get('default_travel_id') or self.env.context.get('active_id')
        if active_travel:
            travel = self.env['corporate.travel'].browse(active_travel)
            res.update({
                'travel_id': travel.id,
                'currency_id': travel.currency_id.id if travel.currency_id else self.env.company.currency_id.id,
                'partner_id': travel.employee_id.user_id.partner_id.id if travel.employee_id and travel.employee_id.user_id.partner_id else travel.employee_id.address_home_id.id if travel.employee_id and travel.employee_id.address_home_id else False,
            })
        return res

    def action_create_payment(self):
        self.ensure_one()
        if not self.journal_id:
            raise UserError(_('Please select a journal.'))
        if self.amount <= 0:
            raise UserError(_('Amount must be positive.'))

        # Determine payment_type: outbound (company pays employee)
        payment_vals = {
            'payment_type': 'outbound',       # company is paying money out
            'amount': self.amount,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'partner_id': self.partner_id.id if self.partner_id else False,
            # partner_type is usually 'supplier' or 'customer'; choose 'supplier' so that payable lines are created.
            # adjust if your DB uses a different convention for employee partners
            'partner_type': 'supplier',
            'currency_id': self.currency_id.id,
            'memo': self.memo or _('Advance payment for travel %s') % (self.travel_id.display_name),
        }

        Payment = self.env['account.payment'].sudo()
        payment = Payment.create(payment_vals)

        # Post the payment (in some Odoo versions it's `post`, in others `action_post`)
        try:
            payment.action_post()
        except Exception:
            try:
                payment.post()
            except Exception:
                # if not available or posting not desired, leave draft
                pass

        # Link payment to travel
        self.travel_id.sudo().write({
            'advance_payment_id': payment.id,
            'advance_amount': self.amount,
            'advance_state': 'paid',
        })

        # Optionally post a chatter message
        self.travel_id.message_post(body=_('Advance payment created: %s (Amount: %s)') % (payment.name or payment.ref or payment.id, self.amount))
        return {'type': 'ir.actions.act_window_close'}
