# -*- coding: utf-8 -*-
{
    'name': "Custom Helpdesk",
    'version': '1.0',
    'category': 'Services/Helpdesk',
    'summary': 'Custom Helpdesk Module with Kanban, Tree, and Form Views',
    'description': """
        A minimal helpdesk module with stages, priority, SLA, and resolution tracking.
        Features:
        • Ticket management with Kanban, List and Form views
        • Stages & Tags
        • Priority & SLA policies
        • Email integration (via mail.thread)
    """,
    'author': "Your Name",
    'website': "https://www.yourcompany.com",
    'license': 'LGPL-3',

    # Core dependencies
    'depends': ['base', 'mail'],

    # Always load these files
    'data': [
        # Security first
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/helpdesk_stage_data.xml',
        'data/helpdesk_tag_data.xml',
        'data/helpdesk_data.xml',

        # Menu (must come before views that reference it)
        'views/helpdesk_menu.xml',

        # Views
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_ticket_kanban.xml',
        'views/helpdesk_team_views.xml',
        'views/helpdesk_templates.xml',
    ],

    # Only load these in demo mode
    'demo': [
        # 'demo/demo_data.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
