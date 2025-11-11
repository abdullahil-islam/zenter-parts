# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression
from odoo.tools import escape_psql


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'analytic.mixin']

    product_brand_id = fields.Many2one(
        "product.brand", 
        string="Brand", 
        help="Select a brand for this product"
    )

    analytic_distribution = fields.Json(
        compute='_compute_analytic_distribution',
        store=True,
        readonly=False,  # Allow manual override if needed
        help="Auto-computed from Brand and Category, but can be manually overridden"
    )
    
    oem_ids = fields.Many2many(
        string="OEM", 
        comodel_name='product.tag', 
        relation='product_template_oem_rel'
    )

    @api.depends('product_brand_id', 'product_brand_id.analytic_distribution', 
                 'categ_id', 'categ_id.analytic_distribution')
    def _compute_analytic_distribution(self):
        """
        Compute analytic distribution from brand and category.
        Brand distribution is applied first, then category overrides.
        """
        for product in self:
            dist = {}
            
            # Apply brand distribution first
            if product.product_brand_id and product.product_brand_id.analytic_distribution:
                dist.update(product.product_brand_id.analytic_distribution)
            
            # Category distribution overrides brand
            if product.categ_id and product.categ_id.analytic_distribution:
                dist.update(product.categ_id.analytic_distribution)
            
            product.analytic_distribution = dist

    @api.model
    def _search_get_detail(self, website, order, options):
        """
        Add description_ecommerce and OEM tags to website shop search.

        This method is called by the website to determine:
        1. Which fields to search (search_fields)
        2. How to display results (mapping, fetch_fields)
        """
        # Get parent configuration
        res = super(ProductTemplate, self)._search_get_detail(website, order, options)

        # Add description_ecommerce to searchable fields
        search_fields = res.get('search_fields', [])
        if 'description_ecommerce' not in search_fields:
            search_fields.append('description_ecommerce')
        res['search_fields'] = search_fields

        # Store the search term in res for later use
        res['search_term'] = options.get('search', '')

        return res

    @api.model
    def _search_build_domain(self, domain_list, search, fields, extra=None):
        """
        Build the search domain including OEM tags logic.

        This is called internally to construct the actual search domain
        from the search term and configured fields.
        
        Fixed: Now properly uses the search parameter for OEM tag matching.
        """
        domains = domain_list.copy()
        
        if search:
            for search_term in search.split(' '):
                subdomains = [[(field, 'ilike', escape_psql(search_term))] for field in fields]
                if extra:
                    subdomains.append(extra(self.env, search_term))

                # OEM tag search
                ProductTag = self.env['product.tag'].sudo()
                matching_tags = ProductTag.search([('name', 'ilike', search_term)])
                if matching_tags:
                    subdomains.append([('oem_ids', 'in', matching_tags.ids)])
                
                domains.append(expression.OR(subdomains))
        
        return expression.AND(domains)

    def _search_fetch(self, search_detail, search, limit, order):
        """
        Fetch products matching the search criteria.

        This method builds the domain and executes the search.
        """
        fields = search_detail['search_fields']
        base_domain = search_detail['base_domain']
        search_domain = self._search_build_domain(
            base_domain, 
            search, 
            fields, 
            search_detail.get('search_extra')
        )

        products = self.search(search_domain, limit=limit, order=order)
        count = len(products)

        return products, count


class ProductProduct(models.Model):
    _inherit = 'product.product'

    oem_ids = fields.Many2many(
        related='product_tmpl_id.oem_ids',
        string="OEM",
        readonly=False
    )
