import argparse
import copy
import importlib.util
import json
import pathlib
import sys
import types
from enum import IntEnum
from unittest.mock import Mock

import pytest
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api = load('integration', 'special_agents/integration.py')
DEVICE = {'id': 'dev-1', 'name': 'Repeated name', 'macAddress': 'AA:BB:CC:DD:EE:FF',
          'state': 'ONLINE', 'interfaces': ['ports'], 'model': 'test'}
SITE = {'id': 'site-1', 'internalReference': 'default', 'name': 'Office'}


def response(payload=None, status=200):
    return Mock(status_code=status, json=Mock(return_value=payload))


def client_with(*responses):
    session = Mock(headers={})
    session.get.side_effect = responses
    return api.IntegrationClient('console.example', 443, 'sensitive-key', True, session), session


def page(data, total=None, offset=0):
    return {'data': data, 'offset': offset, 'totalCount': len(data) if total is None else total}


def test_key_only_get_and_no_redirects():
    client, session = client_with(response({'applicationVersion': '10.6.109'}))
    assert client.get('/v1/info')['applicationVersion'] == '10.6.109'
    assert session.headers['X-API-KEY'] == 'sensitive-key'
    assert session.get.call_args.kwargs['allow_redirects'] is False
    assert session.get.call_args.kwargs['verify'] is True
    session.post.assert_not_called()


@pytest.mark.parametrize('status', [301, 401, 403, 404, 429, 500])
def test_error_status_does_not_leak_key(status):
    client, _ = client_with(response({'secret': 'sensitive-key'}, status))
    with pytest.raises(api.IntegrationError) as error:
        client.get('/v1/info')
    assert 'sensitive-key' not in str(error.value)


@pytest.mark.parametrize('status', [404, 405, 501])
def test_optional_capability(status):
    client, _ = client_with(response(status=status))
    assert client.get('/optional', optional=True) is None


def test_optional_does_not_hide_permission_error():
    client, _ = client_with(response(status=403))
    with pytest.raises(api.IntegrationError):
        client.get('/optional', optional=True)


def test_transport_error_does_not_leak_key():
    client, _ = client_with(requests.ConnectionError('sensitive-key'))
    with pytest.raises(api.IntegrationError, match='Connection or TLS') as error:
        client.get('/v1/info')
    assert 'sensitive-key' not in str(error.value)


def test_pagination_uses_actual_count():
    client, session = client_with(response(page([{'id': 1}], 2)), response(page([{'id': 2}], 2, 1)))
    assert len(client.pages('/v1/sites')) == 2
    assert session.get.call_args_list[1].kwargs['params']['offset'] == 1


def test_empty_page_before_total_fails():
    client, _ = client_with(response(page([], 2)))
    with pytest.raises(api.IntegrationError, match='stopped'):
        client.pages('/v1/sites')


def test_wrong_offset_fails():
    client, _ = client_with(response(page([{}], offset=3)))
    with pytest.raises(api.IntegrationError, match='Malformed'):
        client.pages('/v1/sites')


@pytest.mark.parametrize('selection', [['all'], ['Office'], ['default'], ['site-1']])
def test_collect_site_selection_and_client_count(selection):
    client, session = client_with(
        response({'applicationVersion': '10.6.109'}), response(page([SITE])),
        response(page([{'uplinkDeviceId': 'dev-1'}])), response(page([DEVICE])),
        response({**DEVICE, 'interfaces': {'ports': []}}), response({'uptimeSec': 0}))
    payload = api.collect(client, selection)
    device = payload['sites'][0]['devices'][0]
    assert device['hostname'] == 'unifi-aabbccddeeff'
    assert device['statistics']['uptimeSec'] == 0
    assert device['clientCount'] == 1
    session.post.assert_not_called()


def test_unknown_site_fails_before_publication():
    client, _ = client_with(response({}), response(page([SITE])))
    with pytest.raises(api.IntegrationError, match='not returned'):
        api.collect(client, ['typo'])


def test_offline_skips_statistics_and_preserves_state():
    client, session = client_with(response({}), response(page([SITE])), response(page([])),
        response(page([{**DEVICE, 'state': 'OFFLINE'}])), response(status=404))
    record = api.collect(client, ['all'])['sites'][0]['devices'][0]
    assert record['device']['state'] == 'OFFLINE'
    assert record['statistics'] == {}
    assert len(session.get.call_args_list) == 5


def test_duplicate_mac_fails():
    client, _ = client_with(response({}), response(page([SITE])), response(page([])),
        response(page([DEVICE, DEVICE])), response({}), response({}))
    with pytest.raises(api.IntegrationError, match='Duplicate'):
        api.collect(client, ['all'])


def test_mac_identity_independent_of_name_and_site():
    assert api.device_hostname(DEVICE) == api.device_hostname({**DEVICE, 'name': 'renamed', 'site': 'moved'})
    with pytest.raises(api.IntegrationError):
        api.device_hostname({'macAddress': 'bad\n<<<<injection>>>>'})


@pytest.fixture
def checks(monkeypatch):
    # Minimal Check API stand-ins permit checking decisions without a Checkmk install.
    class State(IntEnum):
        OK = 0
        WARN = 1
        CRIT = 2
        UNKNOWN = 3
    class Object:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
    class Metric:
        def __init__(self, name, value): self.name, self.value = name, value
    v2 = types.ModuleType('cmk.agent_based.v2')
    for name in ['AgentSection', 'CheckPlugin', 'Result', 'Service']:
        setattr(v2, name, Object)
    v2.Metric, v2.State = Metric, State
    monkeypatch.setitem(sys.modules, 'cmk.agent_based.v2', v2)
    return load('checks', 'agent_based/unifi_integration.py')


def record():
    return {'device': copy.deepcopy(DEVICE), 'statistics': {}, 'warnings': [], 'site': SITE, 'clientCount': 0}


def test_missing_stats_never_become_zero_metrics(checks):
    output = list(checks.check_device('Statistics', record()))
    assert not any(isinstance(o, checks.Metric) for o in output)
    assert any(o.state == checks.State.UNKNOWN for o in output)


def test_actual_zero_is_preserved(checks):
    r = record(); r['statistics'] = {'uptimeSec': 0, 'cpuUtilizationPct': 0}
    output = list(checks.check_device('Statistics', r))
    assert {o.name: o.value for o in output if isinstance(o, checks.Metric)} == {'uptime': 0, 'util': 0}


def test_unavailable_details_does_not_break_discovery(checks):
    assert [o.item for o in checks.discover_device(record())] == ['Device', 'Statistics']


def test_offline_device_is_critical(checks):
    r = record(); r['device']['state'] = 'OFFLINE'
    assert list(checks.check_device('Device', r))[0].state == checks.State.CRIT


def test_unused_port_is_not_critical_and_poe_limited_warns(checks):
    r = record()
    r['device']['interfaces'] = {'ports': [{'idx': 1, 'state': 'DOWN', 'poe': {'state': 'LIMITED'}}]}
    output = list(checks.check_device('Port 1', r))
    assert output[0].state == checks.State.OK
    assert output[1].state == checks.State.WARN


def test_parser_preserves_spaces_in_json_strings(checks):
    assert checks.parse_integration([[json.dumps({'name': 'Office North'})]]) == {'name': 'Office North'}


@pytest.fixture
def agent(monkeypatch):
    def module(name, **members):
        obj = types.ModuleType(name); obj.__dict__.update(members)
        monkeypatch.setitem(sys.modules, name, obj)
        return obj
    module('cmk')
    module('cmk.special_agents')
    module('cmk.special_agents.v0_unstable')
    module('cmk.special_agents.v0_unstable.agent_common', SectionWriter=Mock(), special_agent_main=Mock())
    module('cmk.special_agents.v0_unstable.argument_parsing', Args=argparse.Namespace,
           create_default_argument_parser=lambda **kw: argparse.ArgumentParser(**kw))
    secrets = types.SimpleNamespace(lookup=Mock(return_value='sensitive-key'))
    module('cmk.utils', password_store=secrets)
    module('testagent')
    module('testagent.integration', run_integration=api.run_integration)
    return load('testagent.agent_unifi', 'special_agents/agent_unifi.py')


def test_legacy_cli_unchanged(agent):
    args = agent.parse_arguments(['--hostname', 'console', '--username', 'reader', '--password-ref', 'id:file'])
    assert args.username == 'reader' and args.api_key_ref is None


def test_key_cli_needs_no_username(agent):
    args = agent.parse_arguments(['--hostname', 'console', '--api-key-ref', 'id:file'])
    assert args.username is None


@pytest.mark.parametrize('extra', [['--username', 'reader'], ['--udm-pro'], ['--user-piggyback-site']])
def test_key_cli_rejects_legacy_options(agent, extra):
    with pytest.raises(SystemExit):
        agent.parse_arguments(['--hostname', 'console', '--api-key-ref', 'id:file', *extra])


def test_key_and_password_mutually_exclusive(agent):
    with pytest.raises(SystemExit):
        agent.parse_arguments(['--hostname', 'console', '--api-key-ref', 'id:file', '--password', 'pw'])


def test_failed_collect_emits_no_sections_and_closes(agent, monkeypatch, capsys):
    client = Mock()
    monkeypatch.setattr(api, 'IntegrationClient', Mock(return_value=client))
    monkeypatch.setattr(api, 'collect', Mock(side_effect=api.IntegrationError('HTTP 403')))
    args = agent.parse_arguments(['--hostname', 'console', '--api-key-ref', 'id:file'])
    write = Mock(); header = Mock()
    assert api.run_integration(args, write, header) == 1
    write.assert_not_called(); header.assert_not_called(); client.close.assert_called_once()
    assert '403' in capsys.readouterr().err


def test_successful_collect_emits_controller_and_balanced_piggyback(agent, monkeypatch):
    client = Mock()
    r = record(); r['hostname'] = api.device_hostname(DEVICE)
    payload = {'sites': [{'devices': [r]}]}
    monkeypatch.setattr(api, 'IntegrationClient', Mock(return_value=client))
    monkeypatch.setattr(api, 'collect', Mock(return_value=payload))
    args = agent.parse_arguments(['--hostname', 'console', '--api-key-ref', 'id:file', '--device-piggyback'])
    write = Mock(); header = Mock()
    assert api.run_integration(args, write, header) == 0
    assert [c.args[0] for c in write.call_args_list] == ['unifi_integration_controller', 'unifi_integration_device']
    assert [c.args[0] for c in header.call_args_list] == ['unifi-aabbccddeeff', '']


def test_server_side_calls_preserves_secret_references(monkeypatch):
    # Dispatch contract only; native Checkmk Secret rendering is a staging check.
    class Config:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
    calls = types.ModuleType('cmk.server_side_calls.v1')
    calls.Secret = str
    calls.HostConfig = Config
    calls.SpecialAgentCommand = calls.SpecialAgentConfig = Config
    monkeypatch.setitem(sys.modules, 'cmk.server_side_calls.v1', calls)
    server = load('server', 'server_side_calls/agent_unifi.py')
    host = Config(name='controller')
    key = server.UniFiParams(api_key='secret-reference', device_piggyback=True)
    arguments = list(server.agent_unifi_arguments(key, host))[0].command_arguments
    assert arguments == ['--hostname', 'controller', '--port', '443', '--api-key-ref', 'secret-reference', '--device-piggyback']
    login = server.UniFiParams(username='reader', password='password-reference')
    arguments = list(server.agent_unifi_arguments(login, host))[0].command_arguments
    assert '--password-ref' in arguments and '--api-key-ref' not in arguments
    for invalid in [{}, {'api_key': 'ref', 'username': 'reader'}, {'api_key': 'ref', 'password': 'pw'},
                    {'username': 'reader'}, {'api_key': 'ref', 'udm_pro': True}]:
        with pytest.raises(ValueError):
            server.UniFiParams(**invalid)


def test_manifest_matches_installable_archive(tmp_path):
    import ast
    import io
    import tarfile
    builder = load('builder', 'tools/build_mkp.py')
    path = builder.build(tmp_path / 'test.mkp')
    with tarfile.open(path) as outer:
        info = ast.literal_eval(outer.extractfile('info').read().decode())
        assert info == json.load(outer.extractfile('info.json'))
        assert info['name'] == 'unifi'
        assert info['version.min_required'] == '2.5.0p18'
        with tarfile.open(fileobj=io.BytesIO(outer.extractfile('cmk_addons_plugins.tar').read())) as inner:
            assert set(inner.getnames()) == set(info['files']['cmk_addons_plugins'])
            assert inner.getmember('unifi/libexec/agent_unifi').mode == 0o755
            assert 'unifi/special_agents/integration.py' in inner.getnames()
            assert 'unifi/agent_based/unifi_integration.py' in inner.getnames()
            assert not any('__pycache__' in name for name in inner.getnames())


def test_multisite_repeated_display_names_have_distinct_mac_hosts():
    other_site = {**SITE, 'id': 'site-2', 'internalReference': 'branch', 'name': 'Branch'}
    other_device = {**DEVICE, 'id': 'dev-2', 'macAddress': '11:22:33:44:55:66'}
    client, _ = client_with(response({}), response(page([SITE, other_site])),
        response(page([])), response(page([DEVICE])), response({}), response({}),
        response(page([])), response(page([other_device])), response({}), response({}))
    payload = api.collect(client, ['all'])
    assert [s['site']['id'] for s in payload['sites']] == ['site-1', 'site-2']
    assert {s['devices'][0]['hostname'] for s in payload['sites']} == {'unifi-aabbccddeeff', 'unifi-112233445566'}


def test_missing_optional_statistics_reports_capability_warning():
    client, _ = client_with(response({}), response(page([SITE])), response(page([])),
        response(page([DEVICE])), response({}), response(status=404))
    r = api.collect(client, ['all'])['sites'][0]['devices'][0]
    assert r['statistics'] == {}
    assert r['warnings'] == ['Device statistics endpoint unavailable']


def test_bad_json_response_fails():
    bad = response(); bad.json.side_effect = ValueError('sensitive-key')
    client, _ = client_with(bad)
    with pytest.raises(api.IntegrationError, match='Invalid JSON') as error:
        client.get('/v1/info')
    assert 'sensitive-key' not in str(error.value)
