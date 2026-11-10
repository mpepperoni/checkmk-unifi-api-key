"""Read-only local Network Integration API backend (10.6.109 contract)."""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Any
from urllib.parse import quote

import requests
import urllib3

TIMEOUT = 20


class IntegrationError(RuntimeError):
    pass


class IntegrationClient:
    def __init__(self, hostname: str, port: int, key: str, verify: bool, session=None):
        # Hostname is a host, never an arbitrary URL or path.
        if not hostname or any(c in hostname for c in '/?#@\\\r\n'):
            raise IntegrationError("Controller must be a hostname or IP address")
        host = f"[{hostname}]" if ':' in hostname and not hostname.startswith('[') else hostname
        self.base = f"https://{host}:{port}/proxy/network/integration"
        self.verify = verify
        self.session = session if session is not None else requests.Session()
        self.session.headers.update({'X-API-KEY': key, 'Accept': 'application/json'})

    def get(self, path: str, *, params=None, optional=False):
        try:
            response = self.session.get(self.base + path, params=params, timeout=TIMEOUT,
                                        verify=self.verify, allow_redirects=False)
        except requests.RequestException:
            # Do not include response bodies, request objects or credentials in diagnostics.
            raise IntegrationError(f"Connection or TLS failure reading {path}") from None
        status = response.status_code
        if optional and status in (404, 405, 501):
            return None
        if status in (401, 403):
            raise IntegrationError(f"API key rejected or insufficient permission (HTTP {status}) at {path}")
        if status == 429:
            raise IntegrationError("UniFi API rate limit reached; reduce polling frequency")
        if status != 200:
            raise IntegrationError(f"HTTP {status} reading {path}; check Integration API support and console address")
        try:
            payload = response.json()
        except ValueError:
            raise IntegrationError(f"Invalid JSON reading {path}") from None
        if not isinstance(payload, dict):
            raise IntegrationError(f"Expected an object reading {path}")
        return payload

    def pages(self, path: str):
        result = []
        offset = 0
        while True:
            payload = self.get(path, params={'offset': offset, 'limit': 200})
            data = payload.get('data')
            total = payload.get('totalCount')
            if (not isinstance(data, list) or any(not isinstance(row, dict) for row in data)
                    or type(total) is not int or total < 0
                    or payload.get('offset') != offset):
                raise IntegrationError(f"Malformed pagination reading {path}")
            result.extend(data)
            offset += len(data)
            if offset >= total:
                return result
            if not data:
                raise IntegrationError(f"Pagination stopped before totalCount at {path}")
            if offset > 1000000:
                raise IntegrationError(f"Pagination safety limit reached at {path}")

    def close(self):
        self.session.close()


def device_hostname(device):
    mac = device.get('macAddress', '')
    if not isinstance(mac, str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', mac):
        raise IntegrationError("Device has missing or invalid MAC address")
    return 'unifi-' + mac.replace(':', '').lower()


def collect(client, wanted_sites):
    info = client.get('/v1/info')
    sites = client.pages('/v1/sites')
    selected = [s for s in sites if 'all' in wanted_sites or
                set(wanted_sites).intersection(str(s.get(k, '')) for k in ('id', 'internalReference', 'name'))]
    missing = set(wanted_sites) - {'all'} - {str(s.get(k, '')) for s in selected for k in ('id', 'internalReference', 'name')}
    if missing and 'all' not in wanted_sites:
        raise IntegrationError("Configured sites were not returned by this console: " + ', '.join(sorted(missing)))
    if not selected:
        raise IntegrationError("No sites selected or accessible through this console")
    collected = []
    seen = set()
    for site in selected:
        path = '/v1/sites/' + quote(str(site['id']), safe='')
        clients = client.pages(path + '/clients')
        devices = client.pages(path + '/devices')
        records = []
        for device in devices:
            hostname = device_hostname(device)
            if hostname in seen:
                raise IntegrationError("Duplicate device MAC across selected sites")
            seen.add(hostname)
            device_path = path + '/devices/' + quote(str(device['id']), safe='')
            warnings = []
            detail = client.get(device_path, optional=True)
            if detail is None:
                warnings.append('Device details endpoint unavailable')
            stats = {}
            if device.get('state') == 'ONLINE':
                stats = client.get(device_path + '/statistics/latest', optional=True)
                if stats is None:
                    warnings.append('Device statistics endpoint unavailable')
                    stats = {}
            records.append({'device': {**device, **(detail or {})}, 'statistics': stats,
                            'warnings': warnings, 'hostname': hostname, 'site': site,
                            'clientCount': sum(c.get('uplinkDeviceId') == device['id'] for c in clients)})
        collected.append({'site': site, 'devices': records, 'clientCount': len(clients)})
    return {'applicationVersion': info.get('applicationVersion'), 'sites': collected}


def run_integration(args, write_section, piggyback_header):
    from cmk.utils import password_store
    client = None
    try:
        secret_id, secret_file = args.api_key_ref.split(':', 1)
        key = password_store.lookup(pathlib.Path(secret_file), secret_id)
        if not args.no_cert_check:
            verify = True
        else:
            verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        client = IntegrationClient(args.hostname, args.port, key, verify)
        # Collect before emitting, so an API failure cannot publish a partial inventory.
        payload = collect(client, args.sites)
        write_section('unifi_integration_controller', payload)
        if args.device_piggyback:
            for site in payload['sites']:
                for record in site['devices']:
                    piggyback_header(record['hostname'])
                    write_section('unifi_integration_device', record)
                    piggyback_header('')
        return 0
    except (IntegrationError, KeyError, ValueError, OSError):
        # Preserve useful API diagnostics, without rendering secret lookup errors.
        exc = sys.exc_info()[1]
        message = str(exc) if isinstance(exc, IntegrationError) else 'Invalid API key reference or malformed API response'
        sys.stderr.write(f'UniFi Integration API: {message}\n')
        return 1
    finally:
        if client is not None:
            client.close()
