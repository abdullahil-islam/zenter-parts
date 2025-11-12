from odoo import fields, models, _, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_registered_customer = fields.Boolean(default=False)
    # documents related field
    extra_documents = fields.Binary(
        string="Extra Documents",
        related="lead_id.related_extra_documents_id.datas",
    )
