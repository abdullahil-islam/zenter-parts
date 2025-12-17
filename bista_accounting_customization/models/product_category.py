# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'analytic.mixin']

    analytic_distribution = fields.Json(required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    def action_automatic_sync_analytics(self):
        AnalyticPlan = self.env['account.analytic.plan']
        AnalyticAccount = self.env['account.analytic.account']

        # Get eligible plans
        category_plan = AnalyticPlan.search([('is_eligible_prod_categ', '=', True)], limit=1)
        if not category_plan:
            raise UserError("No analytic plan is marked as 'Eligible for Product Family'. Please configure one first.")

        # Pre-fetch all analytic accounts for performance
        category_analytics = {
            aa.name: aa.id
            for aa in AnalyticAccount.search([('plan_id', '=', category_plan.id)])
        }

        Categories = self.env['product.category'].search([])
        analytic_acc_val_list = []
        for category in Categories:
            if not category_analytics.get(category.complete_name, False):
                analytic_acc_val_list.append({
                    'plan_id': category_plan.id,
                    'name': category.complete_name
                })

        if analytic_acc_val_list:
            recs = AnalyticAccount.create(
                analytic_acc_val_list) if analytic_acc_val_list else AnalyticAccount
            category_analytics.update({
                aa.name: aa.id
                for aa in recs
            })

        for category in Categories:
            analytic_distribution = {}
            category_analytic_id = category_analytics.get(category.complete_name)
            if category_analytic_id:
                analytic_distribution[str(category_analytic_id)] = 100
            category.analytic_distribution = analytic_distribution

        return {
            'success': {
                'title': _("Success"),
                'message': _('Success'),
            }
        }

