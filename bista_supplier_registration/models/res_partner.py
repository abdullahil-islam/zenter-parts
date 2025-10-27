from odoo import fields, models, _, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    trading_name = fields.Char(string="Trading Name", help="Trading Name (If different)")
    business_type = fields.Char(string="Type of Business", help="Type of Business (e.g., Ltd, PLC, Inc.)")

    # documents related field
    incorporation_certificate = fields.Binary(
        string="Certificate of Incorporation / Business Registration",
        help="Upload the official Certificate of Incorporation or Business Registration document."
    )
    bank_proof = fields.Binary(
        string="Proof of Bank Account",
        help="Upload bank account verification documents (e.g., IBAN Consult)."
    )
    master_agreement = fields.Binary(
        string="Signed Master Agreement / Framework",
        help="Upload the signed Master Agreement or Framework contract."
    )
    kyc_form = fields.Binary(
        string="KYC Form / Company Financial Structure",
        help="Upload Know Your Customer (KYC) documents or company financial structure details."
    )
    annual_report = fields.Binary(
        string="Annual Report (Latest Available)",
        help="Upload the latest available Annual Report for the company."
    )
    insurance_certificates = fields.Binary(
        string="Insurance Certificates",
        help="Upload valid insurance certificates related to the business."
    )
    other_documents = fields.Binary(
        string="Other Documents",
        help="Upload any other relevant documents not covered in the fields above."
    )

    is_registered_supplier = fields.Boolean(default=False)
    registration_status = fields.Boolean(default=True)

    def grant_portal_access(self):
        """Grant portal access to supplier partner"""
        for partner in self:
            portal_wizard = self.env['portal.wizard'].with_context(
                active_ids=[partner.id]).create({})

            portal_wizard_user = portal_wizard.user_ids
            portal_wizard_user.action_grant_access()

    @api.model
    def create(self, values):
        # Add code here
        return super(ResPartner, self).create(values)
