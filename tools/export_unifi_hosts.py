#!/usr/bin/env python3
"""Export Community Edition host-import CSV from `cmk -d CONTROLLER` output."""
import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path


class ExportError(ValueError):
    pass


def inventory_from_agent_output(text):
    sections = []
    current = None
    for line in text.splitlines():
        if line.startswith('<<<<'):
            current = None
        elif line.startswith('<<<') and line.endswith('>>>'):
            name = line[3:-3].split(':', 1)[0]
            if name == 'unifi_integration_controller':
                current = []
                sections.append(current)
            else:
                current = None
        elif current is not None:
            current.append(line)
    if len(sections) != 1:
        raise ExportError('Expected exactly one unifi_integration_controller section; use cmk -d on the controller host')
    try:
        payload = json.loads('\n'.join(sections[0]))
    except ValueError:
        raise ExportError('Controller inventory section contains invalid JSON') from None
    if not isinstance(payload, dict) or not isinstance(payload.get('sites'), list):
        raise ExportError('Controller inventory has no sites list')
    return payload


def host_rows(payload):
    rows = {}
    try:
        for site in payload['sites']:
            for record in site['devices']:
                device = record['device']
                mac = device['macAddress']
                if not isinstance(mac, str) or not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
                    raise ExportError('Inventory contains an invalid device MAC address')
                hostname = 'unifi-' + mac.replace(':', '').lower()
                if record.get('hostname', hostname) != hostname:
                    raise ExportError('Inventory hostname does not match the MAC-based piggyback name')
                if hostname in rows:
                    raise ExportError('Duplicate device MAC in inventory; export one controller at a time')
                name = device.get('name') or hostname
                if not isinstance(name, str):
                    raise ExportError('Device name must be text')
                # Keep the CSV easy to preview and import, including unusual device names.
                alias = ' '.join(name.split())
                rows[hostname] = (hostname, alias)
    except (KeyError, TypeError, AttributeError):
        raise ExportError('Malformed device inventory') from None
    if not rows:
        raise ExportError('Inventory contains no devices; no CSV was generated')
    return [rows[key] for key in sorted(rows)]


def export_csv(text):
    rows = host_rows(inventory_from_agent_output(text))
    output = io.StringIO(newline='')
    writer = csv.writer(output, delimiter=';', lineterminator='\n')
    writer.writerow(['hostname', 'alias'])
    writer.writerows(rows)
    return output.getvalue(), len(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, help='Saved cmk -d output; default: stdin')
    args = parser.parse_args(argv)
    try:
        text = args.input.read_text(encoding='utf-8') if args.input else sys.stdin.read()
        output, count = export_csv(text)
    except (ExportError, OSError, UnicodeError) as exc:
        print(f'UniFi CSV export failed: {exc}', file=sys.stderr)
        return 1
    sys.stdout.write(output)
    print(f'Exported {count} device hosts. CSV contains hostnames and aliases only.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
