{
    'name': 'Uyscuti Ground Mounted Solar CRM & Proposal',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Dedicated Ground-Mounted Lead Sizing, Dynamic Proposal Calculations, and 25-Year Projection Engine',
    'description': """
        This module provides custom flows and customer proposals for Ground Mounted (GM) Solar leads in CRM.
        Features:
        - Segregated Ground Mounted leads routing.
        - Automated Sizing and Losses estimation (Wheeling & Transmission losses, Scheduling, and Banking charges).
        - Detailed Project Capital Cost, O&M Cost, and Debt/Equity Financing (EMI calculations).
        - Automated generation of a 25-Year Cash Flow Projection matrix.
        - High-fidelity custom proposal views with dynamic layout structures.
        - Beautiful printable PDF quotations.
    """,
    'depends': [
        'crm',
        'sale',
        'uyscuti_crm_custom',
        'uyscuti_solar_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/solar_stage_data.xml',
        'data/solar_photo_type_data.xml',
        'reports/proposal_report.xml',
        'views/crm_lead_views.xml',
        'views/gm_proposal_views.xml',
        'views/sale_order_views.xml',
        'views/solar_project_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
