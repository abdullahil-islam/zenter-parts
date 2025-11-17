# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'analytic.mixin']

    analytic_distribution = fields.Json()

    @api.onchange('country_id')
    def _onchange_country_analytic_distribution(self):
        """
        Update partner's analytic distribution when country changes.
        Merges distributions from all country groups for the selected country.
        """
        if not self.country_id:
            return

        # Get all country groups for this country
        country_groups = self.country_id.country_group_ids
        if not country_groups:
            return

        # Start with existing distribution or empty dict
        distributions = self.analytic_distribution.copy() if self.analytic_distribution else {}

        # Get current company
        company_id = self.env.company.id

        # Merge distributions from all country groups
        for group in country_groups:
            try:
                group_dist = group.get_analytic_distribution(company_id)
                if group_dist:
                    distributions.update(group_dist)
            except Exception as e:
                _logger.warning(
                    "Failed to get analytic distribution from country group %s: %s",
                    group.name, str(e)
                )

        if distributions:
            self.analytic_distribution = distributions

    @api.model_create_multi
    def create(self, vals_list):
        """
        Auto-populate analytic distribution from country groups on partner creation.
        """
        partners = super().create(vals_list)

        for partner in partners:
            # If partner has country but no analytic distribution set, apply country group distribution
            if partner.country_id and not partner.analytic_distribution:
                try:
                    distributions = {}
                    company_id = self.env.company.id

                    for group in partner.country_id.country_group_ids:
                        group_dist = group.get_analytic_distribution(company_id)
                        if group_dist:
                            distributions.update(group_dist)

                    if distributions:
                        partner.analytic_distribution = distributions
                except Exception as e:
                    _logger.warning(
                        "Failed to set country group distribution for partner %s: %s",
                        partner.name, str(e)
                    )

        return partners

    def write(self, vals):
        """
        Override write to handle country changes and update analytic distribution.
        """
        res = super().write(vals)

        # If country_id was changed in this write, update analytic distribution
        if 'country_id' in vals:
            for partner in self:
                if partner.country_id and partner.country_id.country_group_ids:
                    try:
                        distributions = partner.analytic_distribution.copy() if partner.analytic_distribution else {}
                        company_id = self.env.company.id

                        for group in partner.country_id.country_group_ids:
                            group_dist = group.get_analytic_distribution(company_id)
                            if group_dist:
                                distributions.update(group_dist)

                        if distributions != partner.analytic_distribution:
                            # Use context to avoid potential recursion
                            partner.with_context(skip_country_update=True).write({
                                'analytic_distribution': distributions
                            })
                    except Exception as e:
                        _logger.warning(
                            "Failed to update country group distribution for partner %s: %s",
                            partner.name, str(e)
                        )

        return res
