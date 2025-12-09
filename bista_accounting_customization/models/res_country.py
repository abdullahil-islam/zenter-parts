from odoo import api, fields, models
from odoo.exceptions import UserError


class ResCountry(models.Model):
    _inherit = 'res.country'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_country_analytic_accounts()
        return records

    def _create_country_analytic_accounts(self):
        """Create analytic accounts for countries under the eligible country plan."""
        AnalyticAccount = self.env['account.analytic.account']
        AnalyticPlan = self.env['account.analytic.plan']

        # Find the first plan eligible for countries
        country_plan = AnalyticPlan.search([
            ('is_eligible_country', '=', True)
        ], limit=1)

        if not country_plan:
            return  # No eligible plan configured, skip silently

        for country in self:
            # Check if analytic account with same name already exists under this plan
            existing = AnalyticAccount.search([
                ('name', '=', country.name),
                ('plan_id', '=', country_plan.id)
            ], limit=1)

            if not existing:
                AnalyticAccount.create({
                    'name': country.name,
                    'plan_id': country_plan.id,
                })
