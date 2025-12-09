# -*- encoding: utf-8 -*-

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.partner_id and rec.state not in ['draft', 'cancel', 'sent']:
                rec.partner_id._check_proper_contact()
        return res

    def action_quotation_send(self):
        """ Calculate taxes before presenting order to the customer. """
        if self.env.context.get('proforma', False):
            for rec in self:
                if rec.partner_id:
                    rec.partner_id._check_proper_contact()
        return super().action_quotation_send()
