from odoo import fields, models, _, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_registered_customer = fields.Boolean(default=False)
    # documents related field
    address_proof = fields.Binary(
        string="Address Proof",
        help="Upload Address Proof verification documents.",
        attachment=True
    )
    master_agreement = fields.Binary(
        string="Signed Master Agreement / Framework",
        help="Upload the signed Master Agreement or Framework contract.",
        attachment=True
    )
    kyc_form = fields.Binary(
        string="KYC Form / Company Financial Structure",
        help="Upload  Customer (KYC) documents or financial structure details.",
        attachment=True
    )
    extra_documents = fields.Binary(
        string="Extra Documents",
        help="Upload any additional supporting files or reference documents",
        attachment=True,
    )
    other_documents = fields.Binary(
        string="Other Documents",
        help="Upload any other relevant documents not covered in the fields above."
    )
