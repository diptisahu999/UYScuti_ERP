{
    'name': 'Uyscuti Contact Custom',
    'version': '19.0.1.0.0',
    'category': 'Customization',
    'summary': 'Customizations for Contacts',
    'description': """
        This module contains customizations for the Contact (res.partner) form.
        - Makes Phone field required for both Individual and Company.
        - Makes Tags field required for both Individual and Company.
    """,
    'depends': ['base', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
