# -*- coding: utf-8 -*-

{
    'name': 'Sale Backorder Tracking',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Track backordered quantities on sale order lines',
    'description': """
        Sale Backorder Tracking
        =======================
        This module adds a backorder quantity field to sale order lines that displays
        the remaining quantity in backorder deliveries.
        
        Features:
        ---------
        * Displays backordered quantity for each sale order line
        * Automatically updates as backorders are validated
        * Supports multi-warehouse scenarios
    """,
    'author': 'Bista Solutions',
    'website': 'https://www.bistasolutions.com',
    'depends': [
        'sale_stock',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
