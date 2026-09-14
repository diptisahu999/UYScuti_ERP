{
    'name': 'Uyscuti Solar Project Lifecycle',
    'version': '19.0.1.0.0',
    'category': 'Operations',
    'summary': 'Solar Project Stages and Lifecycle Management',
    'description': """
        Management of the solar project lifecycle after Sale Order confirmation.
        Includes stages like Consumer Registration, Document Verification, Installation, 
        Inspections, and Payment Clearance.
    """,
    'depends': ['sale', 'uyscuti_crm_custom', 'uyscuti_sale_custom'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/solar_stage_data.xml',
        'views/solar_project_views.xml',
        'views/solar_permission_views.xml',
        'views/solar_financials_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
