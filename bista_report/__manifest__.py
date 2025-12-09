# -*- encoding: utf-8 -*-

{
    'name': 'Zenter Pdf Reports',
    'version': '18.0.1.0.0',
    'summary': 'Customized PDF report templates',
    'sequence': 1,
    'description': """
This module provides designed PDF report layouts and templates for 
invoices and related accounting documents in Odoo.
    """,
    'author': 'Bista Solutions Inc.',
    'website': 'https://www.bistasolutions.com',
    'company': 'Bista Solutions Inc.',
    'maintainer': 'Bista Solutions Inc.',
    'category': 'Reporting',
    'depends': ['base', 'l10n_us', 'account', 'l10n_ae'],
    'license': 'LGPL-3',
    'data': [
        # Reports
        'report/report_templates.xml',
        'report/report_invoice.xml',
        'data/report_layout.xml',
        'report/document_tax_totals.xml',
        'report/sale_order_reports.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
