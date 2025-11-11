# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SupplierRejectWizard(models.TransientModel):
    _name = 'supplier.reject.wizard'
    _description = 'Supplier Rejection Reason'

    lead_id = fields.Many2one('crm.lead', required=True)
    reason = fields.Text(string="Rejection Reason", required=True)

    def action_confirm(self):
        self.ensure_one()
        lead = self.lead_id.sudo()
        if not lead.is_supplier_reg:
            raise UserError(_("This is not a supplier registration record."))

        lead.write({
            'state': 'rejected',
            'rejection_reason': self.reason,
        })
        lead.message_post(
            body=_("Application Rejected.<br/><b>Reason:</b> %s") % (self.reason or '')
        )
        # Optional: send rejection email if you have a template
        # self.env.ref('bista_supplier_registration.mail_template_supplier_rejected').sudo().send_mail(lead.id, force_send=True)
        return {'type': 'ir.actions.act_window_close'}
