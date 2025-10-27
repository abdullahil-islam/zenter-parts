from odoo import models, fields, api


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'analytic.mixin']

    analytic_distribution = fields.Json()

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        AnalyticAccount = self.env['account.analytic.account'].sudo()
        default_plan = self.env['account.analytic.plan'].search([('is_eligible_customer', '=', True)], limit=1)
        for partner in partners:
            AnalyticAccount.create({
                'name': f"Partner - {partner.name}",
                'partner_id': partner.id,
                'plan_id': default_plan.id,
            })
        return partners
