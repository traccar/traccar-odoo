# Traccar Fleet for Odoo 19 Community

Installable LGPL-3 Odoo add-on. Depends on `fleet` and Python `requests`.

## Features

- Multiple Traccar connections, each scoped to one Odoo company.
- Import devices and latest positions; manual sync and a five-minute scheduled job.
- Explicit one-device-to-one-vehicle mapping, with tracking on the vehicle's Traccar tab.
- Connection status, last contact, GPS fix time/validity, coordinates, address when
  supplied by Traccar, speed in km/h, ignition, and accumulated distance in km.
- Open the selected device in Traccar (separate browser and API URLs supported).
- Optional Fleet odometer logs, calibrated by a km offset and converted to the
  vehicle's km/mile unit. Only increases greater than 0.01 vehicle units are logged.
  Missing/invalid and out-of-order fixes do not write mileage; repeated syncs are safe.
- Devices removed from the account retain their last snapshot and are marked unavailable.
- Network timeouts, sanitized errors, per-server transaction isolation, and a sync lock.

## Setup

1. Put `fleet_traccar` in an Odoo addons directory, restart Odoo, update the Apps
   list, and install **Traccar Fleet** (remove the Apps filter if needed).
2. As an Odoo system administrator, open **Fleet → Traccar → Servers**, create a
   server, and set the base API and browser URLs (without `/api`).
3. Set a bearer token or username/password. Credentials are stored in the Odoo
   database; only system administrators can read those fields or edit connections.
   HTTPS is recommended outside this local test. TLS verification is enabled.
4. Click **Sync now**, then open **Fleet → Traccar → Devices** and link a vehicle.
   Fleet administrators can link devices and sync; Fleet officers can view tracking.
5. Leave **Update vehicle odometer** off until distance and calibration are checked.

When Odoo runs in Docker on macOS with Colima, a Traccar server on the host can
be reached using `http://host.lima.internal:8082`. Set the browser URL separately,
for example `http://localhost:8082` (or port 3000 for the Traccar development UI).
No credentials or test vehicle mappings are included in this add-on.

## Scope and limits

This first version polls snapshots, not a live map or trip/event history. GPS
history stays in Traccar. Last contact/fix timestamps should be used when judging
freshness; offline devices can have old positions and speeds. Device import does
not create vehicles automatically. Fleet officers see devices in their allowed
companies, even when a device is not yet linked. Use a dedicated Traccar account
with only the intended devices when deploying beyond a local test.

Odometer readings use `attributes.totalDistance` (meters), which is accumulated
tracking distance and may differ from a physical odometer. Set an offset to align
it. Counter resets need manual recalibration. Keep the vehicle's odometer unit
consistent after logs exist. The server URL defines the identity of imported IDs;
create a new connection instead of repointing an existing one to another database.

Tested against Odoo Community 19.0-20260817 and the local Traccar REST API.
Other Odoo major versions have not been tested.

## Tests

With this repository on the Odoo addons path, run against a disposable database:

```sh
odoo -d traccar_test -i fleet_traccar --with-demo \
  --stop-after-init --no-http --test-enable --test-tags /fleet_traccar
```

Use `-u fleet_traccar` for subsequent test runs. Supply your deployment's database
connection options and stop any normal Odoo process using the same test database.

Tests cover import idempotency, missing devices, stale/invalid positions, optional
odometer updates, meter/km/mile and knot conversions, repeat/lower readings,
company isolation, secret-field access, officer sync denial, and authentication errors.
