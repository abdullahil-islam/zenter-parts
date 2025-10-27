import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"
    _order = "create_date desc"

    def _assign_and_deactivate_partner(self):
        """Create a partner from contact registration data, link it to the lead"""
        for lead in self:
            partner = lead._create_customer()
            lead.partner_id = partner.id
            lead.partner_id.registration_status = False

    def write(self, vals):
        """Update related partner fields when certain contact fields are changed."""
        res = super().write(vals)
        for lead in self:
            if lead.partner_id:
                partner_vals = {}
                if 'legal_name' in vals:
                    partner_vals['name'] = vals.get('legal_name')
                if 'email_from' in vals:
                    partner_vals['email'] = vals.get('email_from')
                if 'phone' in vals:
                    partner_vals['phone'] = vals.get('phone')
                if partner_vals:
                    lead.partner_id.write(partner_vals)
        return res
