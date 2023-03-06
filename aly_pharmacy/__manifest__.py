# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name": "Pharmacy HCI",
    "version": "14.0.0.3",
    "summary": "Healthcare International Group",
    "description": """
    'Aly El Nemr' developed a module for Pharmacy.
""",
    "depends": ["base", "sale_management", "stock", "account", "aly_basic_hms"],
    # "depends": ["base", "sale_management", "stock", "account_accountant"],
    "data": [
        'security/hospital_groups.xml',
        'security/product_categories_data.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/pharmacy_invoice.xml',
        'views/main_menu_file.xml',
    ],
    "author": "Aly El Nemr",
    "website": "",
    "installable": True,
    "application": True,
    "auto_install": False,
    'icon': '/static/description/icon.jpg',
    "images": ["static/description/Banner.png"],
    "live_test_url": '',

}