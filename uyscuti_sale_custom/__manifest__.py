{
    'name': 'Uyscuti Sale Custom',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Customizations for Sales',
    'description': """
        This module contains customizations for Sales.
        - Removes 'New' button from Quotation List and Kanban views.
    """,
    'depends': ['sale', 'uyscuti_crm_custom'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'uyscuti_sale_custom/static/src/css/sale_order_mobile.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
