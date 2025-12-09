from odoo import models, fields, api


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    analytic_distribution = fields.Json(required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
