# -*- coding: utf-8 -*-
{
    'name': "Keralty",

    'summary': """
        Módulo Keralty creación de Formulario""",

    'description': """
        Módulo Keralty creación de Formulario
    """,

    'author': "Xphera Group S.A.S.",
    'website': "http://xphera.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'stock', 'mrp', 'mail', 'web_kanban_gauge', 'purchase', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/assets.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
