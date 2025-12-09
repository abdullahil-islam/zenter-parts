from odoo import api, fields, models


class ResCountryGroup(models.Model):
    _inherit = 'res.country.group'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_region_analytic_accounts()
        return records

    def _create_region_analytic_accounts(self):
        """Create analytic accounts for country groups under the eligible region plan."""
        AnalyticAccount = self.env['account.analytic.account']
        AnalyticPlan = self.env['account.analytic.plan']

        # Find the first plan eligible for regions
        region_plan = AnalyticPlan.search([
            ('is_eligible_region', '=', True)
        ], limit=1)

        if not region_plan:
            return  # No eligible plan configured, skip silently

        for group in self:
            # Check if analytic account with same name already exists under this plan
            existing = AnalyticAccount.search([
                ('name', '=', group.name),
                ('plan_id', '=', region_plan.id)
            ], limit=1)

            if not existing:
                AnalyticAccount.create({
                    'name': group.name,
                    'plan_id': region_plan.id,
                })
