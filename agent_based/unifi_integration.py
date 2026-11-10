"""Checks for documented Integration API data; no legacy metric defaults."""
import json

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Metric, Result, Service, State


def parse_integration(string_table):
    return json.loads(''.join(' '.join(row) for row in string_table))


agent_section_unifi_integration_controller = AgentSection(
    name='unifi_integration_controller', parse_function=parse_integration)
agent_section_unifi_integration_device = AgentSection(
    name='unifi_integration_device', parse_function=parse_integration)


def discover_controller(section):
    yield Service(item='Application')
    for site in section['sites']:
        yield Service(item=site['site']['id'])


def check_controller(item, section):
    if item == 'Application':
        yield Result(state=State.OK, summary=f"Network {section.get('applicationVersion') or 'unknown'}, sites: {len(section['sites'])}")
        return
    site = next((s for s in section['sites'] if s['site']['id'] == item), None)
    if site is None:
        return
    devices = site['devices']
    offline = sum(d['device'].get('state') in ('OFFLINE', 'ISOLATED', 'CONNECTION_INTERRUPTED') for d in devices)
    other = sum(d['device'].get('state') != 'ONLINE' for d in devices) - offline
    yield Result(state=State.CRIT if offline else State.WARN if other else State.OK,
                 summary=f"{site['site']['name']}: {len(devices)} devices, {offline} unavailable, {other} transitioning, {site['clientCount']} clients")
    yield Metric('unifi_clients', site['clientCount'])
    warnings = sorted({w for d in devices for w in d['warnings']})
    for warning in warnings:
        yield Result(state=State.WARN, summary=warning)


check_plugin_unifi_integration_controller = CheckPlugin(
    name='unifi_integration_controller', service_name='UniFi API %s',
    discovery_function=discover_controller, check_function=check_controller)


def discover_device(section):
    yield Service(item='Device')
    yield Service(item='Statistics')
    interfaces = section['device'].get('interfaces')
    for port in (interfaces if isinstance(interfaces, dict) else {}).get('ports', []):
        yield Service(item=f"Port {port['idx']}")


def check_device(item, section):
    device = section['device']
    if item == 'Device':
        state = device.get('state', 'UNKNOWN')
        severity = State.OK if state == 'ONLINE' else State.CRIT if state in ('OFFLINE', 'ISOLATED', 'CONNECTION_INTERRUPTED') else State.WARN
        yield Result(state=severity, summary=f"{device.get('name')}: {state}, {device.get('model')}, firmware {device.get('firmwareVersion', 'unknown')}, IP {device.get('ipAddress', 'unknown')}")
        if device.get('supported') is False:
            yield Result(state=State.WARN, summary='Device not supported by Network')
        yield Result(state=State.OK, notice=f"Site: {section['site']['name']}; MAC: {device['macAddress']}")
        yield Metric('unifi_clients', section['clientCount'])
    elif item == 'Statistics':
        stats = section.get('statistics', {})
        for warning in section.get('warnings', []):
            yield Result(state=State.WARN, summary=warning)
        if not stats:
            yield Result(state=State.UNKNOWN, summary='Statistics unavailable; device may be offline')
        for key, metric, label, unit in (
            ('uptimeSec', 'uptime', 'Uptime', 's'),
            ('cpuUtilizationPct', 'util', 'CPU', '%'),
            ('memoryUtilizationPct', 'mem_used_percent', 'Memory', '%'),
            ('loadAverage1Min', 'load1', 'Load (1 min)', ''),
            ('loadAverage5Min', 'load5', 'Load (5 min)', ''),
            ('loadAverage15Min', 'load15', 'Load (15 min)', ''),
        ):
            value = stats.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                yield Metric(metric, value)
                yield Result(state=State.OK, summary=f'{label}: {value:g}{unit}')
        # The 10.6.109 contract names these Bps but does not define the unit.
        # Keep raw API values, rather than feeding an assumed unit into if_* counters.
        for key, metric, label in (('rxRateBps', 'unifi_api_uplink_rx_rate', 'Uplink RX'),
                                   ('txRateBps', 'unifi_api_uplink_tx_rate', 'Uplink TX')):
            value = (stats.get('uplink') or {}).get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                yield Metric(metric, value)
                yield Result(state=State.OK, summary=f'{label}: {value:g} API Bps')
        if stats:
            yield Result(state=State.OK, notice='Only statistics supplied by Network are reported')
    elif item.startswith('Port '):
        interfaces = device.get('interfaces')
        port = next((p for p in (interfaces if isinstance(interfaces, dict) else {}).get('ports', []) if str(p['idx']) == item[5:]), None)
        if port is None:
            return
        state = port.get('state', 'UNKNOWN')
        # DOWN can mean an unused port: no invented admin state or link expectation.
        yield Result(state=State.UNKNOWN if state == 'UNKNOWN' else State.OK,
                     summary=f"Link: {state}, speed: {port.get('speedMbps', 'unknown')} Mbit/s, {port.get('connector', 'unknown')}")
        if poe := port.get('poe'):
            poe_state = poe.get('state', 'UNKNOWN')
            yield Result(state=State.WARN if poe_state == 'LIMITED' else State.UNKNOWN if poe_state == 'UNKNOWN' else State.OK,
                         summary=f"PoE: {poe_state}, enabled: {poe.get('enabled')}, {poe.get('standard', 'unknown')}")


check_plugin_unifi_integration_device = CheckPlugin(
    name='unifi_integration_device', service_name='UniFi API %s',
    discovery_function=discover_device, check_function=check_device)
