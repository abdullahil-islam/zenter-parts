# -*- coding: utf-8 -*-
{
    'name': "bista_accounting_customization",

    'summary': "Custom accounting enhancements and analytical features for Odoo",
    'description': """
        Provides custom accounting and analytical enhancements in Odoo,
        including improved reports and integration with products, HR, and analytic accounting.
        
        Key Features:
        - Auto-populate analytic distribution on invoice lines
        - Hierarchical distribution from country groups
        - Product brand and category distribution
        - User and department distribution
        - Enhanced product search with OEM tags
    """,
    'author': "Bista Solutions",
    'website': "https://www.yourcompany.com",

    'category': 'Accounting/Accounting',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'analytic', 'product', 'hr', 'website_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/partner_views.xml',
        'views/product_views.xml',
        'views/product_brand_views.xml',
        'views/product_category_views.xml',
        'views/res_users_views.xml',
        'views/hr_department_views.xml',
        'views/res_country_group_views.xml',  # Added
    ],

    'assets': {
        'web.assets_backend': [
            'bista_accounting_customization/static/src/js/analytic_distribution.js',
        ],
    },
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
