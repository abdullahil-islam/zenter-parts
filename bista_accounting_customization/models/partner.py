# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'analytic.mixin']

    analytic_distribution = fields.Json()

    # @api.onchange('country_id')
    # def _onchange_country_analytic_distribution(self):
    #     """
    #     Update partner's analytic distribution when country changes.
    #     Merges distribution from country groups (respecting hierarchy).
    #     """
    #     if not self.country_id:
    #         return
    #
    #     # Get all country groups for this country
    #     country_groups = self.country_id.country_group_ids
    #     if not country_groups:
    #         return
    #
    #     # Start with existing distribution or empty dict
    #     distributions = self.analytic_distribution.copy() if self.analytic_distribution else {}
    #
    #     # Process each country group
    #     # If multiple groups exist, later ones will override earlier ones
    #     for group in country_groups:
    #         try:
    #             # Get hierarchical distribution (includes parent distributions)
    #             if not group.analytic_distribution:
    #                 raise ValidationError(f'Analytic distribution is not set on the Country Groups [{group.display_name}]')
    #             group_dist = group.get_hierarchical_distribution()
    #             if group_dist:
    #                 distributions.update(group_dist)
    #         except ValidationError as e:
    #             raise ValidationError(str(e))
    #         except Exception as e:
    #             _logger.warning(
    #                 "Failed to get analytic distribution from country group %s: %s",
    #                 group.name, str(e)
    #             )
    #     if distributions:
    #         self.analytic_distribution = distributions
    #
    # # Default plan added in-case no plan found for customer
    # @api.model_create_multi
    # def create(self, vals_list):
    #     partners = super().create(vals_list)
    #     AnalyticAccount = self.env['account.analytic.account'].sudo()
    #     default_plan = self.env['account.analytic.plan'].search(
    #         [('is_eligible_customer', '=', True)], limit=1
    #     )
    #     if not default_plan:
    #         default_plan = self.env['account.analytic.plan'].search([], limit=1)
    #
    #     for partner in partners:
    #         # Create analytic account for partner
    #         AnalyticAccount.create({
    #             'name': f"Partner - {partner.name}",
    #             'partner_id': partner.id,
    #             'plan_id': default_plan.id,
    #         })
    #
    #         # If partner has country but no analytic distribution set, apply country group distribution
    #         if partner.country_id and not partner.analytic_distribution:
    #             try:
    #                 distributions = {}
    #                 for group in partner.country_id.country_group_ids:
    #                     if not group.analytic_distribution:
    #                         raise ValidationError(
    #                             f'Analytic distribution is not set on the Country Groups [{group.display_name}]')
    #                     group_dist = group.get_hierarchical_distribution()
    #                     if group_dist:
    #                         distributions.update(group_dist)
    #
    #                 if distributions:
    #                     partner.analytic_distribution = distributions
    #             except ValidationError as e:
    #                 raise ValidationError(str(e))
    #             except Exception as e:
    #                 _logger.warning(
    #                     "Failed to set country group distribution for partner %s: %s",
    #                     partner.name, str(e)
    #                 )
    #
    #     return partners
    #
    # def write(self, vals):
    #     """
    #     Override write to handle country changes and update analytic distribution.
    #     """
    #     res = super().write(vals)
    #
    #     # If country_id was changed in this write, update analytic distribution
    #     if 'country_id' in vals:
    #         for partner in self:
    #             if partner.country_id and partner.country_id.country_group_ids:
    #                 try:
    #                     distributions = partner.analytic_distribution.copy() if partner.analytic_distribution else {}
    #                     for group in partner.country_id.country_group_ids:
    #                         if not group.analytic_distribution:
    #                             raise ValidationError(
    #                                 f'Analytic distribution is not set on the Country Groups [{group.display_name}]')
    #                         group_dist = group.get_hierarchical_distribution()
    #                         if group_dist:
    #                             distributions.update(group_dist)
    #
    #                     if distributions != partner.analytic_distribution:
    #                         # Use sudo and context to avoid potential permission/recursion issues
    #                         partner.sudo().with_context(skip_country_update=True).write({
    #                             'analytic_distribution': distributions
    #                         })
    #                 except ValidationError as e:
    #                     raise ValidationError(str(e))
    #                 except Exception as e:
    #                     _logger.warning(
    #                         "Failed to update country group distribution for partner %s: %s",
    #                         partner.name, str(e)
    #                     )
    #
    #     return res
