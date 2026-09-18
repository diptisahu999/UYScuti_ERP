# -*- coding: utf-8 -*-
{
    'name': 'Solar O&M Management',
    'version': '1.0',
    'summary': 'Solar Plant Operation & Maintenance Management Module',
    'description': """
        ERP solution for managing Solar Plant Operation & Maintenance activities.
        Manages preventive maintenance, breakdown maintenance, cleaning activities,
        engineer assignments, reports, and plant performance.
    """,
    'category': 'Operations',
    'author': 'Antigravity',
    'depends': [
        'base',
        'mail',
        'sale',
    ],
    'data': [
        'security/solar_om_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/solar_plant_views.xml',
        'views/solar_task_views.xml',
        'views/solar_generation_views.xml',
        'views/sale_order_views.xml',
        'views/dashboard_views.xml',
        'wizard/solar_monthly_generation_wizard_views.xml',
        'views/menus.xml',
        'report/ir_actions_report.xml',
        'report/report_templates.xml',
        'report/generation_report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'solar_om/static/src/components/dashboard/dashboard.js',
            'solar_om/static/src/components/dashboard/dashboard.xml',
            'solar_om/static/src/components/dashboard/dashboard.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
