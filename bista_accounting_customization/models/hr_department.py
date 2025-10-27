from odoo import models, fields


class HrDepartment(models.Model):
    _name = "hr.department"
    _inherit = ['hr.department', 'analytic.mixin']

    analytic_distribution = fields.Json()
