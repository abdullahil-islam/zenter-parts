# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'analytic.mixin']

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account",
        help="Analytic account automatically created for this partner"
    )
    analytic_distribution = fields.Json(compute='_compute_analytic_distribution', store=True)
    # country_group_distribution_ids = fields.One2many('country.group.analytic.distribution', 'country_id')

    @api.depends('country_id', 'analytic_account_id')
    def _compute_analytic_distribution(self):
        for rec in self:
            distributions = {}

            # Add partner's own analytic account
            if rec.analytic_account_id:
                distributions.update({str(rec.analytic_account_id.id):100})

            country_group_distributions = self.env['country.group.analytic.distribution'].sudo().search([
                ('country_id', '=', rec.country_id.id)
            ])
            for group_distribution in country_group_distributions:
                if group_distribution.analytic_distribution:
                    distributions.update(group_distribution.analytic_distribution)
            rec.analytic_distribution = distributions

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._create_analytic_accounts()
        return partners

    def _create_analytic_accounts(self):
        """Create analytic accounts for partners that don't have one."""
        plan = self.env['account.analytic.plan'].sudo().search([
            ('is_eligible_customer', '=', True)
        ], limit=1)

        if not plan:
            # You may want to raise an error or log a warning here
            return

        for partner in self:
            if not partner.analytic_account_id:
                analytic_account = self.env['account.analytic.account'].sudo().create({
                    'name': f"Partner - {partner.name}",
                    'plan_id': plan.id,
                    'partner_id': partner.id,
                })
                partner.analytic_account_id = analytic_account
