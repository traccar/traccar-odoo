{
    'name': 'Traccar Fleet',
    'version': '19.0.1.0.0',
    'summary': 'Connect Fleet vehicles to Traccar GPS tracking',
    'category': 'Human Resources/Fleet',
    'author': 'Traccar',
    'website': 'https://www.traccar.org',
    'support': 'support@traccar.org',
    'price': 0.0,
    'currency': 'EUR',
    'images': ['static/description/device.png', 'static/description/devices.png'],
    'description': '''Connect Odoo Fleet to your Traccar server. Import devices and latest
positions, link vehicles, and optionally synchronize calibrated odometer readings.
The connector authenticates to the configured Traccar server and reads devices
and positions. Tracking snapshots and credentials are stored in your Odoo database.
Opening a device sends its identifier to the configured Traccar web application.
No vendor activation or additional analytics service is used.
''',
    'license': 'LGPL-3',
    'depends': ['fleet'],
    'external_dependencies': {'python': ['requests']},
    'data': ['security/ir.model.access.csv', 'security/rules.xml', 'views/traccar.xml', 'data/cron.xml'],
    'installable': True,
}
