# -*- coding: utf-8 -*-
{
    'name': "Uyscuti Flutter Notification Bridge",
    'version': '19.0.1.0',
    'summary': """
        Intercepts web notifications and sends them to a Flutter WebView app.""",
    'author': "Techvizor",
    'category': 'Extra Tools',
    'depends': [
        'web',  
        'mail', 
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/push_event_data.xml',
        'views/push_device_views.xml',
        'views/push_log_views.xml',
        'views/push_event_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}