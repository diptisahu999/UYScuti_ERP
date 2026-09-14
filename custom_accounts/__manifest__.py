{
    'name': 'Custom Accounts',
    'version': '19.0.1.0',
    'summary': 'Custom Accounts Module Opening Balance and Journal Entry Import, opening debit and credit fields',
    'category': 'Accounting',
    'author': 'Techvizor',
    'description': """
        1. This module adds opening debit and credit fields to account.account model and allows importing journal entries from a CSV file.
        2. This module also provides a wizard for creating opening balance entries.
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/opening_balance_wizard_view.xml',
        'views/account_settings_view.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}