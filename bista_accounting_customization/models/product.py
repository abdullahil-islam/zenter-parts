from odoo import models, fields, api


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'analytic.mixin']

    # analytic_distribution = fields.Json()
    product_brand_id = fields.Many2one(
        "product.brand", string="Brand", help="Select a brand for this product")

    analytic_distribution = fields.Json(
        compute='_compute_analytic_distribution',
        store=True
    )

    @api.depends('product_brand_id', 'categ_id')
    def _compute_analytic_distribution(self):
        for product in self:
            dist = {}
            if product.product_brand_id and product.product_brand_id.analytic_distribution:
                dist.update(product.product_brand_id.analytic_distribution)
            if product.categ_id and product.categ_id.analytic_distribution:
                dist.update(product.categ_id.analytic_distribution)
            product.analytic_distribution = dist
