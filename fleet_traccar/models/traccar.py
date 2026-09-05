import logging
import math
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlencode

import requests

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


def timestamp(value):
    if not value:
        return False
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc).replace(tzinfo=None)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


class TraccarServer(models.Model):
    _name = 'traccar.server'
    _description = 'Traccar Server'
    _check_company_auto = True

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company)
    url = fields.Char('API server URL', required=True, help='Base URL without /api; reachable from the Odoo server.')
    web_url = fields.Char('Browser URL', required=True, help='Base URL reachable from your browser.')
    username = fields.Char(groups='base.group_system', copy=False)
    password = fields.Char(groups='base.group_system', copy=False)
    token = fields.Char('API token', groups='base.group_system', copy=False, help='Optional bearer token; takes precedence over username/password.')
    last_sync = fields.Datetime(readonly=True)
    last_error = fields.Char(readonly=True)
    device_ids = fields.One2many('traccar.device', 'server_id')

    @api.constrains('url', 'web_url')
    def _validate_urls(self):
        for record in self:
            for value in (record.url, record.web_url):
                parsed = urlsplit(value or '')
                if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                    raise ValidationError(_('Use an HTTP(S) base URL without credentials, query parameters, or fragments.'))

    def _get(self, endpoint):
        self.ensure_one()
        secret = self.sudo()
        headers = {'Accept': 'application/json'}
        auth = None
        if secret.token:
            headers['Authorization'] = 'Bearer ' + secret.token
        elif secret.username and secret.password:
            auth = (secret.username, secret.password)
        else:
            raise UserError(_('Configure a Traccar token or username and password.'))
        try:
            response = requests.get(self.url.rstrip('/') + '/api/' + endpoint, headers=headers, auth=auth, timeout=(5, 20), allow_redirects=False)
            if response.status_code in (401, 403):
                raise UserError(_('Traccar rejected the credentials or access permissions.'))
            if response.status_code != 200:
                raise UserError(_('Traccar returned HTTP %s. Check the server URL and permissions.') % response.status_code)
            payload = response.json()
            if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
                raise ValueError('Expected a list of objects')
            return payload
        except requests.RequestException:
            raise UserError(_('Cannot reach Traccar. Check the server URL, network, and TLS certificate.')) from None
        except ValueError:
            raise UserError(_('Traccar returned an invalid API response.')) from None

    def action_sync(self):
        self.ensure_one()
        if not self.env.user.has_group('fleet.fleet_group_manager'):
            raise AccessError(_('Only Fleet administrators can synchronize Traccar.'))
        self.check_access('read')
        self._sync()
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': _('Traccar synchronized'), 'message': _('%s devices available.') % len(self.device_ids),
            'type': 'success', 'next': {'type': 'ir.actions.client', 'tag': 'reload'}}}

    def _sync(self):
        self.ensure_one()
        self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s, %s)', (19790519, self.id))
        if not self.env.cr.fetchone()[0]:
            raise UserError(_('A synchronization is already running. Try again shortly.'))
        devices = self._get('devices')
        positions = {p['deviceId']: p for p in self._get('positions') if p.get('deviceId')}
        Device = self.env['traccar.device']
        existing = {d.remote_id: d for d in Device.search([('server_id', '=', self.id)])}
        seen = set()
        for item in devices:
            remote_id = item.get('id')
            if not isinstance(remote_id, int) or remote_id <= 0 or not item.get('uniqueId'):
                raise UserError(_('Traccar returned an invalid device.'))
            seen.add(remote_id)
            vals = {'name': item.get('name') or item['uniqueId'], 'unique_id': item['uniqueId'],
                    'status': item.get('status') if item.get('status') in ('online', 'offline', 'unknown') else 'unknown',
                    'last_update': timestamp(item.get('lastUpdate')), 'available': True}
            record = existing.get(remote_id)
            if record:
                record.write(vals)
            else:
                record = Device.create(dict(vals, server_id=self.id, remote_id=remote_id))
            position = positions.get(remote_id)
            if position:
                record._apply_position(position)
        for remote_id, record in existing.items():
            if remote_id not in seen:
                record.write({'available': False, 'status': 'unknown'})
        self.sudo().write({'last_sync': fields.Datetime.now(), 'last_error': False})

    @api.model
    def _cron_sync(self):
        for server in self.search([]):
            try:
                with self.env.cr.savepoint():
                    server._sync()
            except Exception as exc:
                # Never persist response bodies or request details containing credentials.
                message = str(exc) if isinstance(exc, UserError) else _('Synchronization failed. Check server logs and configuration.')
                server.write({'last_error': message})
                _logger.warning('Traccar sync failed for server %s (%s)', server.id, type(exc).__name__)


class TraccarDevice(models.Model):
    _name = 'traccar.device'
    _description = 'Traccar Device'
    _order = 'name'
    _check_company_auto = True

    name = fields.Char(required=True, readonly=True)
    server_id = fields.Many2one('traccar.server', required=True, ondelete='cascade', readonly=True)
    company_id = fields.Many2one(related='server_id.company_id', store=True)
    remote_id = fields.Integer('Traccar ID', required=True, readonly=True)
    unique_id = fields.Char('Device identifier', readonly=True)
    available = fields.Boolean('Available in Traccar', default=True, readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', check_company=True, ondelete='set null')
    sync_odometer = fields.Boolean('Update vehicle odometer', help='Use totalDistance plus the offset below. Only higher readings are added; enable after checking calibration.')
    odometer_offset_km = fields.Float('Odometer offset (km)', help='Added to Traccar total distance before converting to the vehicle unit.')
    status = fields.Selection([('online', 'Online'), ('offline', 'Offline'), ('unknown', 'Unknown')], default='unknown', readonly=True)
    last_update = fields.Datetime('Last contact', readonly=True)
    position_time = fields.Datetime('GPS fix time', readonly=True)
    position_id = fields.Integer(readonly=True)
    valid = fields.Boolean('Valid GPS fix', readonly=True)
    latitude = fields.Float(digits=(10, 6), readonly=True)
    longitude = fields.Float(digits=(10, 6), readonly=True)
    speed_kmh = fields.Float('Speed (km/h)', readonly=True)
    address = fields.Char(readonly=True)
    distance_km = fields.Float('Traccar total distance (km)', readonly=True)
    has_distance = fields.Boolean(readonly=True)
    ignition = fields.Selection([('on', 'On'), ('off', 'Off'), ('unknown', 'Unknown')], readonly=True, default='unknown')

    _remote_unique = models.Constraint('UNIQUE(server_id, remote_id)', 'A device can only be imported once per server.')
    _vehicle_unique = models.Constraint('UNIQUE(vehicle_id)', 'A vehicle can only be linked to one Traccar device.')

    @api.constrains('vehicle_id', 'company_id')
    def _same_company(self):
        for record in self:
            if record.vehicle_id and record.vehicle_id.company_id != record.company_id:
                raise ValidationError(_('The vehicle and Traccar server must belong to the same company.'))

    def _apply_position(self, position):
        self.ensure_one()
        when = timestamp(position.get('fixTime'))
        if not when or (self.position_time and when < self.position_time):
            return
        attrs = position.get('attributes') or {}
        lat, lon = number(position.get('latitude')), number(position.get('longitude'))
        valid = bool(position.get('valid')) and lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180
        distance = number(attrs.get('totalDistance'))
        speed = number(position.get('speed'))
        vals = {'position_time': when, 'position_id': position.get('id', 0), 'valid': valid,
                'latitude': lat if valid else 0, 'longitude': lon if valid else 0,
                'speed_kmh': max(0, speed or 0) * 1.852, 'address': position.get('address') or False,
                'has_distance': distance is not None and distance >= 0,
                'distance_km': distance / 1000 if distance is not None and distance >= 0 else 0,
                'ignition': 'on' if attrs.get('ignition') is True else 'off' if attrs.get('ignition') is False else 'unknown'}
        self.write(vals)
        vehicle = self.vehicle_id
        if self.sync_odometer and vehicle and valid and self.has_distance:
            value = self.distance_km + self.odometer_offset_km
            if vehicle.odometer_unit == 'miles':
                value /= 1.609344
            vehicle.invalidate_recordset(['odometer'])
            if value > vehicle.odometer + 0.01:
                self.env['fleet.vehicle.odometer'].create({'vehicle_id': vehicle.id, 'value': value, 'date': when.date()})
                vehicle.invalidate_recordset(['odometer'])

    def action_sync(self):
        self.ensure_one()
        self.check_access('read')
        return self.server_id.action_sync()

    def action_open_traccar(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.act_url', 'target': 'new',
                'url': self.server_id.web_url.rstrip('/') + '/?' + urlencode({'uniqueId': self.unique_id})}


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    traccar_device_ids = fields.One2many('traccar.device', 'vehicle_id', string='Traccar tracking', groups='fleet.fleet_group_user')
