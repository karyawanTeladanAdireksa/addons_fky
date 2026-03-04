{
    'name': 'AOS Web Inherit',
    'license': 'AGPL-3',
    'summary': """
        AOS Web Inherit
        """,
    'version': '0.0.1',
    'category': 'Web',
    'author': 'Alphasoft',
    'description': """
        AOS Web Inherit
    """,
    'depends': [
        'web',
    ],
    'external_dependencies': {'python': [], 'bin': []},
    'qweb':[],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_qweb': [
            'aos_web/static/src/**/*.xml',
        ],
        'web.assets_backend': [
            'aos_web/static/src/webclient/**/*.js',
        ],
    },
    # 'data': [
    #     'views/qweb.xml'
    # ],
    # 'post_init_hook':post_init.
}