{
    'name': 'Custom Payroll Management',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Payroll Management System for Odoo 17 CE',
    'description': """
        Complete payroll management system for Odoo 17 Community Edition
        - Salary rules and structures
        - Employee payroll profiles
        - Nigerian PAYE, Pension, NHF calculations
        - Integration with custom accounting module
    """,
    'author': 'Your Company',
    'website': 'https://yourwebsite.com',
    'depends': [
        'base',
        'hr',
        'custom_accounting_min_backup_20251208_122231',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payroll_sequence.xml',
        'views/salary_rule_views.xml',
        'views/payroll_structure_views.xml',
        'views/employee_profile_views.xml',
        'views/payroll_run_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
