# -*- encoding: utf-8 -*-
{
    'name': 'Bista Zenter Pdf Reports',
    'version': '18.0.1.0.0',
    'summary': 'Customized PDF report templates',
    'description': 'This module provides designed PDF report layouts and templates for invoices and related accounting documents in Odoo.',
    'author': "Bista Solutions",
    'category': 'Reporting',
    'depends': ['base', 'l10n_us', 'account'],
    'data': [
        # Reports
        'report/report_templates.xml',
        'report/report_invoice.xml',
        'data/report_layout.xml',
    ],
    'installable': True,
}
