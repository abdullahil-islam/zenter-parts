from odoo import models, fields


class Users(models.Model):
    _name = "res.users"
    _inherit = ['res.users', 'analytic.mixin']

    analytic_distribution = fields.Json()
