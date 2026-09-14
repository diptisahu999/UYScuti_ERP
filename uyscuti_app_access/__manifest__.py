{
    'name': 'Uyscuti app access',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Customizations for app access',
    'description': """
        This module contains customizations for Sales.
        - Removes 'New' button from Quotation List and Kanban views.
    """,
    'depends': ['sale', 'crm', 'project', 'purchase', 'stock', 'base_accounting_kit', 'dynamic_accounts_report'],
    'data': [
        'security/uyscuti_sale_security.xml',
        'security/uyscuti_purchase_security.xml',
        'security/ir.model.access.csv',
        'data/uyscuti_force_delete_actions.xml',
        'views/ir_ui_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}