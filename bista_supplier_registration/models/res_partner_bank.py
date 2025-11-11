# -*- encoding: utf-8 -*-

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        help="Default payment terms to be applied (e.g., Net 30) when working with this bank account."
    )
    supplier_invoice_currency_id = fields.Many2one(
        "res.currency",
        string="Supplier Invoice Currency",
    )
