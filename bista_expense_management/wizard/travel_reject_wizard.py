from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TravelRejectWizard(models.TransientModel):
    _name = 'travel.reject.wizard'
    _description = 'Travel Rejection Reason'

    travel_id = fields.Many2one('corporate.travel', required=True)
    reason = fields.Text(string="Rejection Reason", required=True)

    def action_confirm(self):
        self.ensure_one()
        if not self.reason:
            raise UserError('Rejection reason is required.')

        user_role = self.env.context.get('user_role', False)
        travel_id = self.travel_id.sudo()

        if user_role == 'MD':
            travel_id.write({'md_rejection_reason': self.reason})
        else:
            travel_id.write({'fd_rejection_reason': self.reason})
        travel_id.message_post(
            body=_("Corporate Travel Rejected by %s.\nReason: %s") % (
                user_role, self.reason or ''
            )
        )
        return {'type': 'ir.actions.act_window_close'}
