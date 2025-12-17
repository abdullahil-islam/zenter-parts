# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    can_edit_discount = fields.Boolean(compute='_compute_can_edit_discount')

    def _compute_can_edit_discount(self):
        for rec in self:
            allowed_groups = ['bista_sale_customization.group_edit_discount_sale_order', 'base.group_system', ]
            rec.can_edit_discount = any(self.env.user.has_group(group) for group in allowed_groups)
