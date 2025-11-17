# -*- coding: utf-8 -*-

{
    'name': "Hide Price In Website",
    'version': '18.0.1.0.0',
    'category': 'Website',
    'sequence': 1,
    'summary': """Hide Price for users in website""",
    'description': """User cannot see Price of the Product in shop page and Price of the Product""",
    'author': 'Bista Solutions Inc.',
    'website': 'https://www.bistasolutions.com',
    'company': 'Bista Solutions Inc.',
    'maintainer': 'Bista Solutions Inc.',
    'depends': ['website_sale', 'website_sale_comparison', 'website_sale_wishlist'],
    'data': [
        'views/product_templates.xml',
        'views/shop_templates.xml',
        'views/res_config_settings_views.xml',
        'views/website_sale_comparison.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

