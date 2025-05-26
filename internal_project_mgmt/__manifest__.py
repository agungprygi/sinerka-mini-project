# -*- coding: utf-8 -*-
{
    'name': "Manajemen Proyek Internal",

    'summary': "Manajemen Proyek Internal",

    'description': """
             Internal Project Management Module
            - Manage internal projects with workflow
            - Task assignment and tracking
            - Project progress monitoring
            - Email notifications for overdue tasks
        """,
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'mail', 'hr'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/automated_actions.xml',
        'views/project_internal_views.xml',
        'views/project_task_internal_views.xml',
        'views/menu_items.xml', 
    ]
}

