# -*- encoding: utf-8 -*-

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.partner_id and rec.state not in ['draft', 'cancel']:
                rec.partner_id._check_proper_contact()
        return res
