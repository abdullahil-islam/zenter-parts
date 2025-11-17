# -*- encoding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

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
