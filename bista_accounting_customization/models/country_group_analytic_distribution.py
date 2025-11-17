# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CountryGroupAnalyticDistribution(models.Model):
    _name = 'country.group.analytic.distribution'
    _description = 'Country Group Analytic Distribution (Company-Specific)'
    _inherit = ['analytic.mixin']

    country_group_id = fields.Many2one(
        'res.country.group',
        string='Country Group',
        required=True,
        ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        required=True
    )

    _sql_constraints = [
        ('country_group_company_uniq',
         'UNIQUE(country_group_id, company_id)',
         'Each country group can only have one analytic distribution per company!')
    ]

    @api.model
    def get_distribution_for_country_group(self, country_group_id, company_id=None):
        """
        Get analytic distribution for a country group in a specific company.

        Args:
            country_group_id: ID of the country group
            company_id: ID of the company (defaults to current company)

        Returns:
            dict: Analytic distribution or empty dict
        """
        if not company_id:
            company_id = self.env.company.id

        mapping = self.search([
            ('country_group_id', '=', country_group_id),
            ('company_id', '=', company_id)
        ], limit=1)

        return mapping.analytic_distribution if mapping else {}
