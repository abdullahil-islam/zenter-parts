# -*- coding: utf-8 -*-
{
    'name': "bista_accounting_customization",

    'summary': "Custom accounting enhancements and analytical features for Odoo",
    'description': """
        Provides custom accounting and analytical enhancements in Odoo,
        including improved reports and integration with products, HR, and analytic accounting.
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

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
    ],

    'assets': {
        'web.assets_backend': [
            'bista_accounting_customization/static/src/js/analytic_distribution.js',
        ],
    }
}
