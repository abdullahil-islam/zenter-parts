# -*- encoding: utf-8 -*-
{
    'name': "Bista Customer Registration",
    'summary': """ Bista Customer Registration (Zenter) """,
    'description': """ Collections of unavailable fields for customer registration (Zenter) """,
    'author': "Bista Solutions",
    'category': 'CRM',
    'version': '18.0.1.0.0',
    'sequence': 1,
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'crm', 'website', 'bista_contact_customization', 'bista_supplier_registration'],
    'data': [
        # "security/ir.model.access.csv",
        "security/customer_security.xml",
        'data/data.xml',
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
        'views/customer_form_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    "application": True,
    "assets": {
    },
}
