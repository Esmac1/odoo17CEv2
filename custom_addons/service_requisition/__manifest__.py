{
    'name': 'Service Requisition',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Manage service requisitions and approvals',
    'description': """
        Service Requisition Management
        ==============================
        This module allows employees to create service requisitions for internal approvals.
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'wizards/reject_wizard_views.xml',
        'views/service_requisition_views.xml',
        'views/service_requisition_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
