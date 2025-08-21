{
    'name': 'Veresiye Defteri',
    'version': '17.0.1.0.0',
    'summary': 'Müşteri veresiye takibi',
    'author': 'Your Company',
    'category': 'Accounting',
    'depends': ['base', 'product', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/ledger_views.xml',
        'views/partner_views.xml',
        'views/menu_views.xml',
        'views/payment_wizard_views.xml',
        'report/receipt_report.xml',
    ],
    'installable': True,
    'application': True,
}
