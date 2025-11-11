# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    partner_id = fields.Many2one(
        'res.partner', 
        string="Partner",
        help="Link this analytic account to a specific partner"
    )


class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    # Eligibility flags to control which entities can use which plans
    is_eligible_customer = fields.Boolean(
        string="Eligible for Customers",
        default=False,
        help="If checked, this plan can be used in customer analytic distributions"
    )
    is_eligible_product = fields.Boolean(
        string="Eligible for Products",
        default=False,
        help="If checked, this plan can be used in product analytic distributions"
    )
    is_eligible_prod_brand = fields.Boolean(
        string="Eligible for Product Brands",
        default=False,
        help="If checked, this plan can be used in product brand analytic distributions"
    )
    is_eligible_prod_categ = fields.Boolean(
        string="Eligible for Product Categories",
        default=False,
        help="If checked, this plan can be used in product category analytic distributions"
    )
    is_eligible_hr_department = fields.Boolean(
        string="Eligible for HR Departments",
        default=False,
        help="If checked, this plan can be used in department analytic distributions"
    )
    is_eligible_region = fields.Boolean(
        string="Eligible for Regions",
        default=False,
        help="If checked, this plan can be used in country group analytic distributions"
    )
    is_eligible_top_region = fields.Boolean(
        string="Eligible for Top-Level Regions",
        default=False,
        help="If checked, this plan can be used for parent-level country groups"
    )

    @api.model
    def get_relevant_plans(self, **kwargs):
        """
        Filter analytic plans based on the model context.
        
        This ensures that only relevant plans are shown in the analytic distribution
        widget for each specific entity type.
        """
        res = super().get_relevant_plans(**kwargs)

        model_eligibility_map = {
            'res.partner': 'is_eligible_customer',
            'product.template': 'is_eligible_product',
            'product.brand': 'is_eligible_prod_brand',
            'product.category': 'is_eligible_prod_categ',
            'hr.department': 'is_eligible_hr_department',
            'res.country.group': 'is_eligible_region',
        }

        current_model = kwargs.get('current_model', '')
        
        if current_model in model_eligibility_map:
            eligibility_field = model_eligibility_map[current_model]
            data = []
            
            for plan in res:
                rec = self.env['account.analytic.plan'].sudo().browse(plan['id'])
                if rec and getattr(rec, eligibility_field, False):
                    data.append(plan)
            
            return data

        return res
