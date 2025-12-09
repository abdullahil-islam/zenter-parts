# -*- coding: utf-8 -*-

from odoo import fields, models, _, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    skip_backorder = fields.Boolean(string="Skip Backorder", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list):
            if not rec.is_company and rec.parent_id:
                rec.skip_backorder = rec.parent_id.skip_backorder
            if rec.is_company and 'skip_backorder' in vals:
                for child in rec.child_ids:
                    child.skip_backorder = vals['skip_backorder']
        return records

    def write(self, vals):
        """Override write method to handle customer group changes."""
        for rec in self:
            if not rec.is_company and rec.parent_id:
                vals['skip_backorder'] = rec.parent_id.skip_backorder
            if rec.is_company and 'skip_backorder' in vals:
                for child in rec.child_ids:
                    child.skip_backorder = vals['skip_backorder']
        return super().write(vals)
