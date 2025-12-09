# -*- coding: utf-8 -*-

{
    'name': "Product Classification",
    'license': 'LGPL-3',
    'summary': "Product Brand and OEM Classification Management",
    'description': """
        Provides product classification features including:
        - Product Brand management with analytic distribution
        - OEM (Original Equipment Manufacturer) tags for products
        - Enhanced product search with OEM tag matching
        - Brand-based product organization
        
        This module can be used independently or as part of a larger
        product catalog management system.
    """,
    'author': 'Bista Solutions Inc.',
    'website': 'https://www.bistasolutions.com',
    'company': 'Bista Solutions Inc.',
    'maintainer': 'Bista Solutions Inc.',

    'category': 'Sales/Product',
    'version': '18.0.1.0.0',
    'sequence': 1,
    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'stock', 'analytic', 'website_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/product_brand_views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}

