{
    'name': 'Veresiye Defteri',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'sequence': 95,
    'summary': 'Kontak bazlı veresiye borç takip sistemi',
    'description': """
    Veresiye Defteri Modülü
    =======================
    
    * Müşteri bazlı veresiye borç yönetimi
    * Ürün, adet, fiyat satırları ile borç kaydı
    * Kısmi ve tam ödeme takibi
    * 80mm POS fiş yazdırma desteği
    * Muhasebeden bağımsız çalışma
    """,
    'author': 'ProlifeSoft',
    'website': 'https://www.prolifesoft.com',
    'license': 'Other OSI approved licence',
    'depends': ['base', 'product'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence.xml',
        'data/paperformat.xml',
        
        # Views
        'views/ledger_views.xml',
        'views/partner_views.xml',
        'wizard/payment_wizard_views.xml',
        
        # Reports
        'report/receipt_report.xml',
        'report/partner_list_report.xml',
        
        # Menu
        'views/menu.xml',
    ],
    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
