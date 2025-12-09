# -*- encoding: utf-8 -*-

{
    'name': "Customer Registration",
    'summary': """ Bista Customer Registration (Zenter) """,
    'description': """ Collections of unavailable fields for customer registration (Zenter) """,
    'author': 'Bista Solutions Inc.',
    'website': 'https://www.bistasolutions.com',
    'company': 'Bista Solutions Inc.',
    'maintainer': 'Bista Solutions Inc.',
    'category': 'CRM',
    'version': '18.0.1.0.0',
    'sequence': 1,
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'crm', 'website', 'purchase', 'bista_supplier_registration', 'base_vat'],
    'data': [
        # "security/ir.model.access.csv",
        "security/customer_security.xml",
        'data/data.xml',
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
        'views/customer_form_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'bista_customer_registration/static/src/js/customer_registration_form.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    "application": True,
}
