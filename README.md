# Traccar for Odoo

Odoo Community 19 integration with Traccar GPS tracking. The `fleet_traccar`
add-on imports devices and their latest positions, links them to Fleet vehicles,
and optionally records calibrated odometer readings.

## Features

- Company-scoped Traccar connections and vehicle links
- Manual and scheduled synchronization every five minutes
- GPS position, last contact, status, speed, ignition, and accumulated distance
- Optional odometer updates with kilometer/mile conversion
- Links to the selected device in the Traccar web app

See [the module documentation](fleet_traccar/README.md) for configuration,
permissions, and limitations.

## Installation

Add this repository directory to Odoo's `addons_path`, restart Odoo, update the
Apps list, then install **Traccar Fleet**. The add-on requires the `fleet` module
and Python `requests`.

For Docker, mount the repository at `/mnt/extra-addons` in an Odoo 19 container.
Configure connections in **Fleet → Traccar → Servers**, sync, then link vehicles
in **Fleet → Traccar → Devices**.

## Development

Restart Odoo after Python changes. Upgrade the module after model, view, or data
changes. Run the tests against a disposable Odoo database with Fleet installed:

```sh
odoo -d traccar_test -i fleet_traccar --with-demo \
  --stop-after-init --no-http --test-enable --test-tags /fleet_traccar
```

For an existing test database, use `-u fleet_traccar` instead of `-i`. The tests
mock Traccar responses and do not require a running Traccar server. Database
connection and addons-path options depend on your Odoo deployment.

## License

[LGPL-3.0](LICENSE). The accompanying GPL-3.0 text is in [COPYING](COPYING).
