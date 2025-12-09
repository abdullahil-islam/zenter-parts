# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplateInherit(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'analytic.mixin']

    analytic_distribution = fields.Json(
        compute='_compute_analytic_distribution',
        store=True,
        readonly=False,  # Allow manual override if needed
        help=("Auto-computed from Brand and Category, "
              "but can be manually overridden")
    )

    @api.depends(
        'product_brand_id',
        'product_brand_id.analytic_distribution',
        'categ_id',
        'categ_id.analytic_distribution'
    )
    def _compute_analytic_distribution(self):
        """
        Compute analytic distribution from brand and category.
        Brand distribution is applied first, then category overrides.

        Note: product_brand_id field is provided by
        bista_product_classification module.
        """
        for product in self:
            dist = {}

            # Apply brand distribution first
            if (product.product_brand_id and
                    product.product_brand_id.analytic_distribution):
                dist.update(product.product_brand_id.analytic_distribution)

            # Category distribution overrides brand
            if (product.categ_id and
                    product.categ_id.analytic_distribution):
                dist.update(product.categ_id.analytic_distribution)

            product.analytic_distribution = dist
