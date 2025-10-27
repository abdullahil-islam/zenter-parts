from odoo import fields, models, api


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    partner_id = fields.Many2one('res.partner', string="Partner")


class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    is_eligible_customer = fields.Boolean(default=False)
    is_eligible_product = fields.Boolean(default=False)
    is_eligible_prod_brand = fields.Boolean(default=False)
    is_eligible_prod_categ = fields.Boolean(default=False)
    is_eligible_user = fields.Boolean(default=False)
    is_eligible_hr_department = fields.Boolean(default=False)

    @api.model
    def get_relevant_plans(self, **kwargs):
        res = super().get_relevant_plans(**kwargs)

        if 'current_model' in kwargs and kwargs.get('current_model', '') in ['res.partner', 'product.template', 'product.brand', 'product.category', 'res.users', 'hr.department']:
            data = []
            for plan in res:
                rec = self.env['account.analytic.plan'].sudo().browse(plan['id'])
                if not rec:
                    continue

                if kwargs.get('current_model', '') == 'res.partner' and rec.is_eligible_customer:
                    data.append(plan)
                elif kwargs.get('current_model', '') == 'product.template' and rec.is_eligible_product:
                    data.append(plan)
                elif kwargs.get('current_model', '') == 'product.brand' and rec.is_eligible_prod_brand:
                    data.append(plan)
                elif kwargs.get('current_model', '') == 'product.category' and rec.is_eligible_prod_categ:
                    data.append(plan)
                elif kwargs.get('current_model', '') == 'res.users' and rec.is_eligible_user:
                    data.append(plan)
                elif kwargs.get('current_model', '') == 'hr.department' and rec.is_eligible_hr_department:
                    data.append(plan)
            return data

        return res
