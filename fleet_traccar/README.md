# Traccar Fleet

Connect Traccar devices to Odoo 19 Community Fleet vehicles. Requires the `fleet`
module and Python `requests`.

## Installation

Copy `fleet_traccar` into an Odoo addons directory, restart Odoo, update the Apps
list, and install **Traccar Fleet**. Remove the Apps filter if the module is not
shown.

## Configuration

1. As an Odoo system administrator, open **Fleet → Traccar → Servers** and create
   a connection for the appropriate company.
2. Enter the base API and browser URLs, without `/api`. The API URL must be
   reachable from the Odoo server; the browser URL must be reachable by users.
3. Enter a bearer token or username and password. Use HTTPS and a dedicated
   Traccar account with access to the intended devices.
4. Click **Sync now**, then open **Fleet → Traccar → Devices** and link each device
   to its Fleet vehicle. The device and vehicle must belong to the same company.

Synchronization runs every five minutes by default. Tracking details are also
available on the vehicle's **Traccar** tab. **Open in Traccar** opens the selected
device in the configured Traccar web application.

## Odometer updates

**Update vehicle odometer** is disabled by default. Before enabling it, compare
Traccar's total distance with the vehicle's odometer and set **Odometer offset
(km)** to align them.

Readings use Traccar's `totalDistance` attribute in meters, plus the offset,
converted to the vehicle's kilometer or mile unit. Only increases greater than
0.01 vehicle units are recorded. Repeated imports do not duplicate readings;
invalid or older GPS fixes do not add odometer logs.

Counter resets require recalibration. Keep the vehicle's odometer unit consistent
after logs exist.

## Access and data

- System administrators configure connections and can read credential fields.
- Fleet administrators link vehicles and synchronize devices.
- Fleet officers can view devices in their allowed companies, including unlinked
  devices.

Credentials and tracking snapshots are stored in the Odoo database. The connector
reads device and position data from the configured Traccar server. Opening a
device in the browser passes its identifier to the configured Traccar web app.

## Limitations

The module imports the latest tracking snapshot. GPS history remains in Traccar;
live maps, trip reports, and event history are not included. Check the last contact
and GPS fix timestamps: offline devices may show old locations and speeds.

Importing devices does not create vehicles. Devices that become unavailable in
Traccar retain their last snapshot and are marked unavailable in Odoo.

Create a new connection when switching to a different Traccar database, since
device IDs are specific to each database.

Supports Odoo 19 Community. Other Odoo major versions have not been tested.

## License

[LGPL-3.0](LICENSE).
