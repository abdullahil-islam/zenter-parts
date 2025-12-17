# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CountryGroupAnalyticDistribution(models.Model):
    _name = 'country.group.analytic.distribution'
    _description = 'Country Group Analytic Distribution (Company-Specific)'
    _inherit = ['analytic.mixin']

    # country_group_id = fields.Many2one(
    #     'res.country.group',
    #     string='Country Group',
    #     required=True,
    #     ondelete='cascade'
    # )
    # allowed_country_ids = fields.Many2many('res.country', related='country_group_id.country_ids')
    country_id = fields.Many2one(
        'res.country',
        string='Country',
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
    #
    # _sql_constraints = [
    #     ('country_group_company_uniq',
    #      'UNIQUE(country_group_id, company_id)',
    #      'Each country group can only have one analytic distribution per company!')
    # ]

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

    def action_syc_country_analytics(self):
        Country = self.env['res.country']
        CountryGroup = self.env['res.country.group']
        AnalyticPlan = self.env['account.analytic.plan']
        AnalyticAccount = self.env['account.analytic.account']

        # Get eligible plans
        country_plan = AnalyticPlan.search([('is_eligible_country', '=', True)], limit=1)
        region_plan = AnalyticPlan.search([('is_eligible_region', '=', True)], limit=1)
        if not country_plan:
            raise UserError("No analytic plan is marked as 'Eligible for Country'. Please configure one first.")

        if not region_plan:
            raise UserError("No analytic plan is marked as 'Eligible for Region'. Please configure one first.")

        # Pre-fetch all analytic accounts for performance
        country_analytics = {
            aa.name: aa.id
            for aa in AnalyticAccount.search([('plan_id', '=', country_plan.id)])
        }
        region_analytics = {
            aa.name: aa.id
            for aa in AnalyticAccount.search([('plan_id', '=', region_plan.id)])
        }

        countries = Country.search([])
        regions = CountryGroup.search([])
        analytic_acc_val_list = []
        for country in countries:
            if not country_analytics.get(country.name, False):
                analytic_acc_val_list.append({
                    'plan_id': country_plan.id,
                    'name': country.name
                })
        for region in regions:
            if not region_analytics.get(region.name, False):
                analytic_acc_val_list.append({
                    'plan_id': region_plan.id,
                    'name': region.name
                })
        if analytic_acc_val_list:
            recs = AnalyticAccount.create(analytic_acc_val_list) if analytic_acc_val_list else AnalyticAccount

        return {
            'success': {
                'title': _("Success"),
                'message': _('Success'),
            }
        }


    def action_automatic_entry(self):
        # Bulk create Country Analytic Distribution records
        # Links each country to its analytic account + all its country groups' analytic accounts

        CountryAnalytic = self.env['country.group.analytic.distribution']
        Country = self.env['res.country']
        CountryGroup = self.env['res.country.group']
        AnalyticAccount = self.env['account.analytic.account']
        AnalyticPlan = self.env['account.analytic.plan']

        current_company = self.env.company

        # Get eligible plans
        country_plan = AnalyticPlan.search([('is_eligible_country', '=', True)], limit=1)
        region_plan = AnalyticPlan.search([('is_eligible_region', '=', True)], limit=1)

        if not country_plan:
            raise UserError("No analytic plan is marked as 'Eligible for Country'. Please configure one first.")

        if not region_plan:
            raise UserError("No analytic plan is marked as 'Eligible for Region'. Please configure one first.")

        # Pre-fetch all analytic accounts for performance
        country_analytics = {
            aa.name: aa.id
            for aa in AnalyticAccount.search([('plan_id', '=', country_plan.id)])
        }
        region_analytics = {
            aa.name: aa.id
            for aa in AnalyticAccount.search([('plan_id', '=', region_plan.id)])
        }

        # Get existing country IDs for current company (to skip)
        existing_country_ids = CountryAnalytic.search([
            ('company_id', '=', current_company.id)
        ]).mapped('country_id').ids

        # Get all countries without existing records
        countries = Country.search([('id', 'not in', existing_country_ids)])

        if not countries:
            raise UserError("All countries already have analytic distribution records for %s" % current_company.name)

        # Build mapping: country -> country groups
        # In Odoo, res.country.group has country_ids (Many2many to res.country)
        country_to_groups = {}
        all_groups = CountryGroup.search([])
        for group in all_groups:
            for country in group.country_ids:
                if country.id not in country_to_groups:
                    country_to_groups[country.id] = []
                country_to_groups[country.id].append(group.name)

        vals_list = []
        skipped_countries = []

        for country in countries:
            analytic_distribution = {}

            # 1. Add country's analytic account
            str_analytic_ids = ''
            country_analytic_id = country_analytics.get(country.name)
            if country_analytic_id:
                str_analytic_ids = str(country_analytic_id)

            # 2. Add all country groups' analytic accounts
            group_names = country_to_groups.get(country.id, [])
            first_group_added = False
            for group_name in group_names:
                region_analytic_id = region_analytics.get(group_name)
                if region_analytic_id and not first_group_added:
                    str_analytic_ids += ',' + str(region_analytic_id)
                    first_group_added = True
                elif region_analytic_id:
                    analytic_distribution[str(region_analytic_id)] = 100
            analytic_distribution[str(str_analytic_ids)] = 100

            # Only create if we have at least the country analytic
            if not analytic_distribution:
                skipped_countries.append(country.name)
                continue

            vals_list.append({
                'country_id': country.id,
                'company_id': current_company.id,
                'analytic_distribution': analytic_distribution,
            })

        # Batch create
        created_records = CountryAnalytic.create(vals_list) if vals_list else CountryAnalytic

        # Summary message
        msg_parts = []
        if created_records:
            msg_parts.append("Successfully created %d analytic distribution records for %s." % (len(created_records),
                                                                                                current_company.name))
        if skipped_countries:
            msg_parts.append("Skipped %d countries (no matching analytic accounts): %s" % (len(skipped_countries),
                                                                                           ', '.join(
                                                                                               skipped_countries[:10])))
            if len(skipped_countries) > 10:
                msg_parts[-1] += '...'

        return {
            'warning': {
                'title': _("Information"),
                'message': _('\n\n'.join(msg_parts)),
            }
        }
