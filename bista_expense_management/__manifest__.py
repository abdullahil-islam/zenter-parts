
{
    'name': 'Corporate Travel Approval',
    'version': '1.0.0',
    'summary': 'Estimate and approve corporate travel costs (MD -> FD approvals)',
    'description': 'Corporate travel request form with multi-level approval and expense creation.',
    'author': 'Generated',
    'category': 'Human Resources/Expenses',
    'depends': ['base', 'mail', 'hr', 'hr_expense'],
    'data': [
        'security/corporate_travel_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/corporate_travel_views.xml',
        'data/sequence_data.xml',
        'wizard/travel_reject_wizard_views.xml',
        'wizard/travel_diem_expense_wizard_views.xml',
        'views/menu.xml',
        'views/travel_expense_category_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
}
