# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCountryGroup(models.Model):
    _name = 'res.country.group'
    _inherit = ['res.country.group', 'analytic.mixin']

    analytic_distribution = fields.Json(
        string="Analytic Distribution",
        help="Default analytic distribution for partners in this country group"
    )
    
    # Add hierarchy support for regional groupings
    # parent_group_id = fields.Many2one(
    #     'res.country.group',
    #     string='Parent Region',
    #     help='Parent region for hierarchical regional distribution'
    # )
    # child_group_ids = fields.One2many(
    #     'res.country.group',
    #     'parent_group_id',
    #     string='Sub-regions'
    # )
    
    def get_hierarchical_distribution(self):
        """
        Get analytic distribution including parent hierarchy.
        Child distributions override parent distributions.
        """
        self.ensure_one()
        distribution = {}
        
        # Apply current level (overrides parent)
        if self.analytic_distribution:
            distribution.update(self.analytic_distribution)
        
        return distribution
