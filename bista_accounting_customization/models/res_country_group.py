# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCountryGroup(models.Model):
    _inherit = 'res.country.group'

    analytic_distribution_ids = fields.One2many(
        'country.group.analytic.distribution',
        'country_group_id',
        string='Analytic Distributions',
        help='Company-specific analytic distributions for this country group'
    )

    analytic_distribution_count = fields.Integer(
        string='Distribution Count',
        compute='_compute_analytic_distribution_count'
    )

    @api.depends('analytic_distribution_ids')
    def _compute_analytic_distribution_count(self):
        for group in self:
            group.analytic_distribution_count = len(group.analytic_distribution_ids)

    def get_analytic_distribution(self, company_id=None):
        """
        Get analytic distribution for this country group in a specific company.

        Args:
            company_id: ID of the company (defaults to current company)

        Returns:
            dict: Analytic distribution or empty dict
        """
        self.ensure_one()
        if not company_id:
            company_id = self.env.company.id

        DistributionModel = self.env['country.group.analytic.distribution'].sudo()
        return DistributionModel.get_distribution_for_country_group(self.id, company_id)
