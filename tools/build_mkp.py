#!/usr/bin/env python3
"""Build an MKP using the upstream python-mkp archive layout, with stdlib only."""
import io
import json
import pathlib
import pprint
import tarfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION = '2026.11.10-api-key.1'
DIRECTORIES = ('agent_based', 'graphing', 'inventory_ui', 'libexec', 'rulesets',
               'server_side_calls', 'special_agents')


def add_bytes(archive, name, payload, mode=0o644):
    entry = tarfile.TarInfo(name)
    entry.size, entry.mode, entry.mtime = len(payload), mode, 0
    archive.addfile(entry, io.BytesIO(payload))


def build(destination=None):
    paths = [ROOT / '__init__.py']
    for directory in DIRECTORIES:
        paths.extend(p for p in (ROOT / directory).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    files = {f'unifi/{p.relative_to(ROOT).as_posix()}': p for p in sorted(paths)}
    files['unifi/LICENSE'] = ROOT / 'LICENSE'
    files['unifi/API_KEY_SETUP.md'] = ROOT / 'API_KEY_SETUP.md'
    info = {
        'name': 'unifi', 'version': VERSION,
        'title': 'UniFi special agent with local Integration API key support',
        'author': 'Local fork of the Checkmk Extensions UniFi project',
        'description': 'Adds local API-key monitoring based on Network 10.6.109. Experimental: validate on Checkmk 2.5.0p18 before production.',
        'download_url': 'https://gitlab.com/checkmk-extensions/unifi/',
        'version.packaged': '2.5.0p18', 'version.min_required': '2.5.0p18',
        'version.usable_until': '2.6.0',
        'files': {'cmk_addons_plugins': list(files)}, 'num_files': len(files),
    }
    inner = io.BytesIO()
    with tarfile.open(fileobj=inner, mode='w') as archive:
        for name, path in files.items():
            add_bytes(archive, name, path.read_bytes(), 0o755 if path.parent.name == 'libexec' else 0o644)
    destination = pathlib.Path(destination) if destination else ROOT / 'dist' / f'unifi-{VERSION}.mkp'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(destination, mode='w:gz') as archive:
        add_bytes(archive, 'info', pprint.pformat(info).encode())
        add_bytes(archive, 'info.json', json.dumps(info).encode())
        add_bytes(archive, 'cmk_addons_plugins.tar', inner.getvalue())
    return destination


if __name__ == '__main__':
    print(build())
