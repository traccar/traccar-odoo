{
    'name': 'Traccar Fleet',
    'version': '19.0.1.0.0',
    'summary': 'Connect Fleet vehicles to Traccar GPS tracking',
    'category': 'Human Resources/Fleet',
    'author': 'Traccar integration contributors',
    'license': 'LGPL-3',
    'depends': ['fleet'],
    'external_dependencies': {'python': ['requests']},
    'data': ['security/ir.model.access.csv', 'security/rules.xml', 'views/traccar.xml', 'data/cron.xml'],
    'installable': True,
}
