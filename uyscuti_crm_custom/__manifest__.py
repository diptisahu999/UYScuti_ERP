{
    'name': 'Uyscuti CRM Custom',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Customizations for CRM',
    'description': """
        This module contains customizations for CRM.
        - Removes 'Enrich' button.
        - Removes 'Property 1' (lead_properties) field.
    """,
    'depends': [
        'crm', 
        'crm_iap_enrich',
        'hr_timesheet',
        'survey',
        'hr_attendance',
        'hr_holidays',
        # 'data_cleaning',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/hide_menus.xml',
        'views/solar_master_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
