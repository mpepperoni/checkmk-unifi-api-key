import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('hosts_csv', Path(__file__).resolve().parents[1] / 'tools/export_unifi_hosts.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def record(mac, name='Office switch'):
    return {'device': {'macAddress': mac, 'name': name, 'state': 'OFFLINE'}}


def agent_output(records, header='<<<unifi_integration_controller:sep(0)>>>'):
    return header + '\n' + json.dumps({'sites': [{'devices': records}]}) + '\n<<<other>>>\nignored\n'


def test_matches_piggyback_names_includes_offline_and_quotes_alias():
    output, count = exporter.export_csv(agent_output([
        record('AA:BB:CC:DD:EE:FF', 'Switch; "North"'), record('11:22:33:44:55:66', 'AP')]))
    assert count == 2
    assert list(csv.reader(io.StringIO(output), delimiter=';')) == [
        ['hostname', 'alias'], ['unifi-112233445566', 'AP'], ['unifi-aabbccddeeff', 'Switch; "North"']]


def test_200_devices_and_cached_section_header():
    records = [record(f'00:00:00:00:00:{i:02x}', f'Device {i}') for i in range(200)]
    output, count = exporter.export_csv(agent_output(records, '<<<unifi_integration_controller:cached(123,60):sep(0)>>>'))
    assert count == 200 and len(output.splitlines()) == 201


def test_multiple_sites_and_repeated_names():
    payload = {'sites': [{'devices': [record('00:11:22:33:44:55', 'AP')]},
                         {'devices': [record('00:11:22:33:44:66', 'AP')]}]}
    assert len(exporter.host_rows(payload)) == 2


@pytest.mark.parametrize('text', ['', '<<<other>>>\n{}', '<<<unifi_integration_controller>>>\ninvalid',
    agent_output([]), agent_output([record('invalid')]),
    agent_output([record('AA:BB:CC:DD:EE:FF'), record('aa:bb:cc:dd:ee:ff')]),
    agent_output([record('AA:BB:CC:DD:EE:FF')]) * 2])
def test_bad_inventory_fails_without_csv(text):
    with pytest.raises(exporter.ExportError):
        exporter.export_csv(text)


def test_cli_error_outputs_no_partial_csv(tmp_path, capsys):
    source = tmp_path / 'input'; source.write_text(agent_output([record('invalid')]))
    assert exporter.main([str(source)]) == 1
    result = capsys.readouterr()
    assert result.out == '' and 'failed' in result.err


def test_cli_success_count_only_on_stderr(tmp_path, capsys):
    source = tmp_path / 'input'; source.write_text(agent_output([record('AA:BB:CC:DD:EE:FF', 'Café AP')]))
    assert exporter.main([str(source)]) == 0
    result = capsys.readouterr()
    assert result.out.startswith('hostname;alias\n') and 'Café AP' in result.out
    assert 'Exported 1' in result.err


def test_alias_whitespace_and_missing_name():
    rows = exporter.host_rows({'sites': [{'devices': [record('AA:BB:CC:DD:EE:FF', 'Office\n North'),
                                                     record('00:11:22:33:44:55', '')]}]})
    assert rows == [('unifi-001122334455', 'unifi-001122334455'), ('unifi-aabbccddeeff', 'Office North')]
