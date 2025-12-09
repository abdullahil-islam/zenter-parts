# -*- encoding: utf-8 -*-

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.partner_id and rec.state not in ['draft', 'cancel', 'sent']:
                rec.partner_id._check_proper_contact()
        return res

    def action_rfq_send(self):
        """ Calculate taxes before presenting order to the customer. """
        return super(PurchaseOrder, self.with_context(skip_check_proper_contact=True)).action_rfq_send()

