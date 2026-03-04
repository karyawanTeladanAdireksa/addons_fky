{
    'name': 'AOS Barcode Adireksa',
    'license': 'AGPL-3',
    'summary': """
        AOS Barcode Adireksa
        """,
    'version': '0.0.1',
    'category': 'Barcode',
    'author': 'Alphasoft',
    'description': """
        AOS Barcode Adireksa
    """,
    'depends': [
        'stock',
        'stock_barcode',
        'adireksa_do_slip'
    ],
    'external_dependencies': {'python': [], 'bin': []},
    'data': [
    ],
    'qweb':[],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_qweb': [
            # 'aos_barcode_inherit/static/src/**/*.xml',
            # 'aos_barcode_adireksa/static/src/xml/barcode_main.xml'
        ],
    }
        
    # 'post_init_hook':post_init.
}