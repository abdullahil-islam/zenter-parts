from odoo import models, fields


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'analytic.mixin']

    analytic_distribution = fields.Json()
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
