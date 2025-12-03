# -*- encoding: utf-8 -*-

from odoo import fields, models, _, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_registered_customer = fields.Boolean(default=False)
    extra_documents = fields.Binary(
        string="Extra Documents",
        related="lead_id.related_extra_documents_id.datas",
    )
    distributor_or_customer = fields.Selection(
        [('distributor', 'Distributor'), ('customer', 'Customer')],
        string='Registration Type',
        help='Type of registration: Distributor or Customer'
    )
