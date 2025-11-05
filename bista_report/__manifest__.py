# -*- encoding: utf-8 -*-
{
    'name': 'Bista Zenter Pdf Reports',
    'version': '18.0.1.0.0',
    'summary': '',
    'category': 'Reporting',
    'description': 'Bista Zenter Pdf Reports',
    'depends': ['base', 'account'],
    'data': [
        # Reports
        'report/report_templates.xml',
        'report/report_invoice.xml',
        'data/report_layout.xml',
    ],
    'installable': True,
}
