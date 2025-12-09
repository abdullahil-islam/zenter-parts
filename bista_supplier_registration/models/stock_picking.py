# -*- encoding: utf-8 -*-

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.partner_id and rec.state not in ['draft', 'cancel']:
                rec.partner_id._check_proper_contact()
        return res

    def button_validate(self):
        """ Override to skip backorder if partner has skip_backorder set """
        if self.partner_id and self.partner_id.skip_backorder:
            if not self.env.context.get('skip_backorder', False) and not self.env.context.get(
                    'picking_ids_not_to_backorder', False):
                return super().with_context(skip_backorder=True,
                                            picking_ids_not_to_backorder=self.ids).button_validate()
        return super().button_validate()
