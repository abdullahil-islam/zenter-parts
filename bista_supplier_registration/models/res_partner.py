# -*- encoding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account",
        help="Analytic account automatically created for this partner"
    )
    trading_name = fields.Char(string="Trading Name", help="Trading Name (If different)")
    business_type = fields.Char(string="Type of Business", help="Type of Business (e.g., Ltd, PLC, Inc.)")

    lead_id = fields.Many2one('crm.lead', string="Related Lead", help="Link to the related CRM lead for this supplier.")

    # documents related field
    incorporation_certificate = fields.Binary(
        string="Certificate of Incorporation / Business Registration",
        related="lead_id.related_incorporation_certificate_id.datas",
    )
    bank_proof = fields.Binary(
        string="Proof of Bank Account",
        related="lead_id.related_bank_proof_id.datas",
    )
    master_agreement = fields.Binary(
        string="Signed Master Agreement / Framework",
        related="lead_id.related_master_agreement_id.datas",
    )
    kyc_form = fields.Binary(
        string="KYC Form / Company Financial Structure",
        related="lead_id.related_kyc_form_id.datas",
    )
    annual_report = fields.Binary(
        string="Annual Report (Latest Available)",
        related="lead_id.related_annual_report_id.datas",
    )
    insurance_certificates = fields.Binary(
        string="Insurance Certificates",
        related="lead_id.related_insurance_certificates_id.datas",
    )
    other_documents = fields.Binary(
        string="Other Documents",
        related="lead_id.related_other_documents_id.datas",
    )

    is_registered_supplier = fields.Boolean(default=False)
    registration_status = fields.Boolean(default=True)

    def grant_portal_access(self):
        """Grant portal access to supplier partner"""
        for partner in self:
            portal_wizard = self.env['portal.wizard'].with_context(
                active_ids=[partner.id]).create({})

            portal_wizard_user = portal_wizard.user_ids
            for user in portal_wizard_user:
                user.action_grant_access()

    def _check_proper_contact(self):
        """Ensure that the partner has at least one contact with email and phone"""
        if not self.env.context.get('skip_check_proper_contact', False):
            for rec in self:
                partner = rec
                if rec.parent_id:
                    partner = rec.parent_id
                if not partner.registration_status:
                    if not partner.is_registered_customer or not partner.is_registered_supplier:
                        raise UserError(
                            _("The contact registration has not been approved. Please complete the registration process to proceed."))
                if partner.registration_status:
                    missing_fields = []
                    check_vals = [
                        'name',
                        'street',
                        'city',
                        'zip',
                        'vat',
                        'country_id',
                        'email',
                        'phone',
                    ]
                    if self.env['res.country.state'].search([('country_id', '=', partner.country_id.id)], limit=1):
                        check_vals.append('state_id')
                    if partner.supplier_rank > 0 and partner.is_registered_supplier:
                        check_vals.append('property_supplier_payment_term_id')
                    if not partner.bank_ids:
                        check_vals.append('bank_ids')
                    if not partner.parent_id and partner.company_type == 'company':
                        if not self.env['res.partner'].search([('parent_id', '=', partner.id), ('type', '=', 'contact')]):
                            check_vals.append('child_ids')
                    for field in check_vals:
                        if not partner[field]:
                            missing_fields.append(field)

                    if missing_fields:
                        field_labels = [partner._fields[f].string for f in missing_fields if f in partner._fields]
                        raise UserError(
                            _("The following required fields in the contact are missing or empty: %s") % (', '.join(field_labels))
                        )
