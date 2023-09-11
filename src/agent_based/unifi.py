#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
#  _   _       _  __ _ 
# | | | |     (_)/ _(_)
# | | | |_ __  _| |_ _ 
# | | | | '_ \| |  _| |
# | |_| | | | | | | | |
#  \___/|_| |_|_|_| |_|
#
# created: 01/2022
#
# Author: Frank Baier
# E-Mail: dev@baier-nt.de
#
from __future__ import annotations

from cmk.gui.i18n import _
from dataclasses import dataclass
from cmk.base.api.agent_based.inventory_classes import TableRow
from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    Attributes,
    check_levels,
    HostLabel,
    Metric,
    register,
    Result,
    Service,
    State,
    type_defs,
)
from cmk.base.plugins.agent_based.utils import if64, interfaces
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
)
import json

Section = Optional[Dict]

UNIFI_DEVICE_STATES = {
    0: "disconnected",
    1: "connected",
    2: "pending"
}

UNIFI_DEVICE_TABLE: dict[str, str] = {
    'BZ2': 'UAP',
    'BZ2LR': 'UAP-LR',
    'U2HSR': 'UAP-Outdoor+',
    'U2IW': 'UAP-IW',
    'U2L48': 'UAP-AC-LR',
    'U2Lv2': 'UAP-AC-LR',
    'U2M': 'UAP-Mini',
    'U2O': 'UAP-Outdoor',
    'U2S48': 'UAP-AC',
    'U2Sv2': 'UAP-AC',
    'U5O': 'UAP-Outdoor5',
    'U7E': 'UAP-AC',
    'U7EDU': 'UAP-AC-EDU',
    'U7Ev2': 'UAP-AC',
    'U7HD': 'UAP-AC-HD',
    'U7SHD': 'UAP-AC-SHD',
    'U7NHD': 'UAP-nanoHD',
    'UFLHD': 'UAP-FlexHD',
    'UHDIW': 'UAP-IW-HD',
    'UAIW6': 'U6-IW',
    'UAE6': 'U6-Extender',
    'UAL6': 'U6-Lite',
    'UAM6': 'U6-Mesh',
    'UALR6': 'U6-LR-EA',
    'UAP6': 'U6-LR',
    'UALR6v2': 'U6-LR',
    'UALR6v3': 'U6-LR',
    'UCXG': 'UAP-XG',
    'UXSDM': 'UWB-XG',
    'UXBSDM': 'UWB-XG-BK',
    'UCMSH': 'UAP-XG-Mesh',
    'U7IW': 'UAP-AC-IW',
    'U7IWP': 'UAP-AC-IW-Pro',
    'U7MP': 'UAP-AC-M-Pro',
    'U7LR': 'UAP-AC-LR',
    'U7LT': 'UAP-AC-Lite',
    'U7O': 'UAP-AC-Outdoor',
    'U7P': 'UAP-Pro',
    'U7MSH': 'UAP-AC-M',
    'U7PG2': 'UAP-AC-Pro',
    'p2N': 'PICOM2HP',
    'UDMB': 'UAP-BeaconHD',
    'USF5P': 'USW-Flex',
    'US8': 'US-8',
    'US8P60': 'US-8-60W',
    'US8P150': 'US-8-150W',
    'S28150': 'US-8-150W',
    'USC8': 'US-8',
    'USC8P60': 'US-8-60W',
    'USC8P150': 'US-8-150W',
    'US16P150': 'US-16-150W',
    'S216150': 'US-16-150W',
    'US24': 'US-24-G1',
    'US24PRO': 'USW-Pro-24-PoE',
    'US24PRO2': 'USW-Pro-24',
    'US24P250': 'US-24-250W',
    'US24PL2': 'US-L2-24-PoE',
    'US24P500': 'US-24-500W',
    'S224250': 'US-24-250W',
    'S224500': 'US-24-500W',
    'US48': 'US-48-G1',
    'US48PRO': 'USW-Pro-48-PoE',
    'US48PRO2': 'USW-Pro-48',
    'US48P500': 'US-48-500W',
    'US48PL2': 'US-L2-48-PoE',
    'US48P750': 'US-48-750W',
    'S248500': 'US-48-500W',
    'S248750': 'US-48-750W',
    'US6XG150': 'US-XG-6PoE',
    'USMINI': 'USW-Flex-Mini',
    'USXG': 'US-16-XG',
    'USC8P450': 'USW-Industrial',
    'UDC48X6': 'USW-Leaf',
    'USL8A': 'UniFi Switch Aggregation',
    'USAGGPRO': 'UniFi Switch Aggregation Pro',
    'USL8LP': 'USW-Lite-8-PoE',
    'USL8MP': 'USW-Mission-Critical',
    'USL16P': 'USW-16-PoE',
    'USL16LP': 'USW-Lite-16-PoE',
    'USL24': 'USW-24-G2',
    'USL48': 'USW-48-G2',
    'USL24P': 'USW-24-PoE',
    'USL48P': 'USW-48-PoE',
    'UGW3': 'USG-3P',
    'UGW4': 'USG-Pro-4',
    'UGWHD4': 'USG',
    'UGWXG': 'USG-XG-8',
    'UDM': 'UDM',
    'UDMSE': 'UDM-SE',
    'UDMPRO': 'UDM-Pro',
    'UP4': 'UVP-X',
    'UP5': 'UVP',
    'UP5t': 'UVP-Pro',
    'UP7': 'UVP-Executive',
    'UP5c': 'UVP',
    'UP5tc': 'UVP-Pro',
    'UP7c': 'UVP-Executive',
    'UCK': 'UCK',
    'UCK-v2': 'UCK',
    'UCK-v3': 'UCK',
    'UCKG2': 'UCK-G2',
    'UCKP': 'UCK-G2-Plus',
    'UASXG': 'UAS-XG',
    'ULTE': 'U-LTE',
    'ULTEPUS': 'U-LTE-Pro',
    'ULTEPEU': 'U-LTE-Pro',
    'UP1': 'USP-Plug',
    'UP6': 'USP-Strip',
    'USPPDUP': 'USP - Power Distribution Unit Pro',
    'USPRPS': 'USP-RPS',
    'US624P': 'UniFi6 Switch 24',
    'UBB': 'UBB',
    'UXGPRO': 'UniFi NeXt-Gen Gateway PRO'
}


def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def host_labels(section: Dict) -> type_defs.HostLabelGenerator:
    devtype = section.get("type")
    devtype2 = section.get("ubnt_device_type")
    if devtype:
        yield HostLabel(u'unifi_device_type', devtype)
    elif devtype2:
        yield HostLabel(u'unifi_device_type', devtype2)


def parse_unifi(string_table: type_defs.StringTable) -> Section:
    if string_table:
        data = json.loads(string_table[0][0])
        assert isinstance(data, dict)
        return data
    return None


# ***************************** UNIFI SITES *****************************

def discover_unifi_controller_sites(
        section: Section,
) -> type_defs.DiscoveryResult:
    for site in section:
        yield Service(item=site.get('desc'))
        for data in site.get('health'):
            if data.get('status') != 'unknown':
                yield Service(item=f"%s %s" % (site.get('desc'), data.get('subsystem')))


def check_unifi_controller_sites(
        item: str,
        section: Section,
) -> type_defs.CheckResult:
    for site in section:
        if item == site.get('desc'):
            yield Result(state=State.OK, summary=f"Site description: %s" % site.get('desc'))
            yield Result(state=State.OK, summary=f"Site id: %s" % site.get('name'))
            yield Result(state=State.OK, summary=f"Alarms: %s" % site.get('num_new_alarms'))

        for data in site.get('health'):
            if item == f"%s %s" % (site.get('desc'), data.get('subsystem')):
                yield Result(state=State.OK, summary=f"Status: %s" % data.get('status'))
                yield Result(state=State.OK, summary=f"adopted Devices: %s" % data.get('num_adopted'))
                yield Result(state=State.OK, summary=f"pending Devices: %s" % data.get('num_pending'))
                yield Result(state=State.OK, summary=f"disconnected Devices: %s" % data.get('num_disconnected'))
                if data.get('num_disabled') is not None:
                    yield Result(state=State.OK, summary=f"disabled Devices: %s" % data.get('num_disabled'))
                yield Result(state=State.OK, summary=f"Users: %s" % data.get('num_user', 0))
                yield Result(state=State.OK, summary=f"Guests: %s" % data.get('num_guest', 0))
                yield Metric("user-num_sta", int(data.get('num_user', 0)))
                yield Metric("guest-num_sta", int(data.get('num_guest', 0)))


register.agent_section(
    name="unifi_controller_sites",
    parse_function=parse_unifi,
    # host_label_function=host_labels,
)

register.check_plugin(
    name="unifi_controller_sites",
    sections=["unifi_controller_sites"],
    service_name="Unifi Site %s",
    discovery_function=discover_unifi_controller_sites,
    check_function=check_unifi_controller_sites,
)


# ***************************** UNIFI CONTROLLER *****************************

def discover_unifi_controller(
        section: Section,
) -> type_defs.DiscoveryResult:
    yield Service()


def check_unifi_controller(
        section: Section,
) -> type_defs.CheckResult:
    yield Result(state=State.OK, summary=f"Name: %s" % section.get('name'))
    yield Result(state=State.OK, summary=f"Type: %s" % section.get('ubnt_device_type'))
    yield Result(state=State.OK, summary=f"Build: %s" % section.get('build'))

    if section.get('unsupported_device_count') == 0:
        yield Result(state=State.OK, summary=f"Unsupported devices: %s" % section.get('unsupported_device_count'))
        yield Result(state=State.OK, notice=f"Unsupported devices:  %s" % section.get('unsupported_device_list'))
    else:
        yield Result(state=State.WARN, summary=f"Unsupported devices: %s" % section.get('unsupported_device_count'))
        yield Result(state=State.WARN, notice=f"Unsupported devices:  %s" % section.get('unsupported_device_list'))


register.agent_section(
    name="unifi_controller",
    parse_function=parse_unifi,
    host_label_function=host_labels,
)

register.check_plugin(
    name="unifi_controller",
    sections=["unifi_controller"],
    service_name="Unifi Controller",
    discovery_function=discover_unifi_controller,
    check_function=check_unifi_controller,
)


# ***************************** UNIFI CONTROLLER HEALTH *****************************

def discover_unifi_site_controller_health(
        section: Section,
) -> type_defs.DiscoveryResult:
    for data in section:
        if data.get('status') != 'unknown':
            yield Service(item=f"%s" % data.get('subsystem'))


def check_unifi_site_controller_health(
        item: str,
        section: Section,
) -> type_defs.CheckResult:
    for data in section:
        if item == f"%s" % data.get('subsystem'):
            yield Result(state=State.OK, summary=f"Status: %s" % data.get('status'))
            if data.get('num_adopted') is not None:
                yield Result(state=State.OK, summary=f"adopted Devices: %s" % data.get('num_adopted'))
            if data.get('num_pending') is not None:
                if data.get('num_pending') == 0:
                    yield Result(state=State.OK, summary=f"pending Devices: %s" % data.get('num_pending'))
                else:
                    yield Result(state=State.WARN, summary=f"pending Devices: %s" % data.get('num_pending'))

            if data.get('num_disconnected') is not None:
                if data.get('num_disconnected') == 0:
                    yield Result(state=State.OK, summary=f"disconnected Devices: %s" % data.get('num_disconnected'))
                else:
                    yield Result(state=State.WARN, summary=f"disconnected Devices: %s" % data.get('num_disconnected'))

            if data.get('num_disabled') is not None:
                yield Result(state=State.OK, summary=f"disabled Devices: %s" % data.get('num_disabled'))
            yield Result(state=State.OK, summary=f"Users: %s" % data.get('num_user', 0))
            yield Result(state=State.OK, summary=f"Guests: %s" % data.get('num_guest', 0))
            yield Metric("user-num_sta", int(data.get('num_user', 0)))
            yield Metric("guest-num_sta", int(data.get('num_guest', 0)))


register.agent_section(
    name="unifi_site_controller_health",
    parse_function=parse_unifi,
)

register.check_plugin(
    name="unifi_site_controller_health",
    sections=["unifi_site_controller_health"],
    service_name="Unifi Health %s",
    discovery_function=discover_unifi_site_controller_health,
    check_function=check_unifi_site_controller_health,
)


# ***************************** UNIFI DEVICE (Piggyback) *****************************

def discover_unifi_device(
        section: Section,
) -> type_defs.DiscoveryResult:
    devtype = section.get("type")
    # name = section.get("name")
    if devtype:
        yield Service(item='Device')
    if section.get('has_temperature', False) or section.get('has_fan'):
        yield Service(item='Environment')


def check_unifi_device(
        item: str,
        section: Section,
) -> type_defs.CheckResult:
    if item == 'Device':
        yield Result(state=State.OK, summary=f"Type: %s" % section.get('type'))
        yield Result(state=State.OK, summary=f"Model: %s" % UNIFI_DEVICE_TABLE.get(section.get('model'),
                                                                                   section.get('model', 'unknown')))
        yield Result(state=State.OK, summary=f"Serial: %s" % section.get('serial'))
        yield Result(state=State.OK, summary=f"Version: %s" % section.get('version'))
        yield Result(state=State.OK, summary=f"Name: %s" % section.get('name'))
        yield Result(state=State.OK, summary=f"IP: %s" % section.get('ip'))
        yield Result(state=State.OK, summary=f"Satisfaction: %s%%" % int(section.get('satisfaction', 0)))
        yield Metric(name="satisfaction", value=int(section.get('satisfaction', 0)), boundaries=(0, 100))

        if section.get('state') == 1:
            yield Result(state=State.OK,
                         summary=f"State: %s" % UNIFI_DEVICE_STATES.get(section.get('state'), 'unknown'))
        else:
            yield Result(state=State.CRIT,
                         summary=f"State: %s" % UNIFI_DEVICE_STATES.get(section.get('state'), 'unknown'))

        if section.get('adopted'):
            yield Result(state=State.OK, summary=f"adopted")
        else:
            yield Result(state=State.WARN, summary=f"waiting for adoption")

        yield Result(state=State.WARN if section.get('model_in_eol') else State.OK,
                     notice=f"Model in EOL: %s" % section.get('model_in_eol'))
        yield Result(state=State.WARN if section.get('model_in_lts') else State.OK,
                     notice=f"Model in LTS: %s" % section.get('model_in_lts'))
        yield Result(state=State.WARN if section.get('model_incompatible') else State.OK,
                     notice=f"Model incompatible: %s" % section.get('model_incompatible'))

        if section.get('jumboframe_enabled', False):
            yield Result(state=State.OK, notice=f"Jumbo-Frames: enabled")
        else:
            yield Result(state=State.OK, notice=f"Jumbo-Frames: disabled")

    elif item == 'Environment':
        if section.get('has_temperature') and section.get('general_temperature') is not None:
            temperature = round(float(section.get('general_temperature')), 1)
            if section.get('overheating'):
                yield Result(state=State.CRIT, summary=f'Temperature: {temperature:.1f}°C (overheating)')
            else:
                yield Result(state=State.OK, summary=f'Temperature: {temperature:.1f}°C')

            yield Metric(name="temperature", value=temperature)
            yield Result(state=State.OK, summary=f'Temperature: {temperature:.1f}°C')

        if section.get('has_fan'):
            yield Result(state=State.OK, summary=f"Fan-Level: %s%%" % section.get('fan_level'))


register.agent_section(
    name="unifi_device",
    parse_function=parse_unifi,
    host_label_function=host_labels,
)

register.check_plugin(
    name="unifi_device",
    sections=["unifi_device"],
    service_name="Unifi Device %s",
    discovery_function=discover_unifi_device,
    check_function=check_unifi_device,
)


# ***************************** UNIFI INTERFACE (Piggyback) *****************************

@dataclass
class UnifiInterface(interfaces.Interface):
    jumbo: bool = False
    satisfaction: int = 0
    port_poe: bool = False
    poe_enable: bool = False
    poe_mode: Optional[str] = None
    poe_good: Optional[bool] = None
    poe_current: Optional[float] = 0
    poe_power: Optional[float] = 0
    poe_voltage: Optional[float] = 0
    poe_class: Optional[str] = None
    dot1x_mode: Optional[str] = None
    dot1x_status: Optional[str] = None
    ip_address: Optional[str] = None
    portconf: Optional[str] = None

    def __post_init__(self) -> None:
        self.finalize()


def _convert_unifi_counters_if(section: Section | List) -> interfaces.Section:
    return [
        UnifiInterface(
            # index=str(line.get('port_idx')),
            index=str(line.get('port_idx')) if str(line.get('port_idx')).isdecimal() else str(idx),
            descr=line.get('name'),
            alias=line.get('name'),
            type='6',  # Ethernet
            # speed=if64.fix_if_64_highspeed(line.get('speed')),
            speed=line.get('speed', 0) * 1000000,
            oper_status='1' if line.get('up') else '2',
            in_octets=_safe_int(line.get('rx_bytes', 0)),
            in_ucast=_safe_int(line.get('rx_packets', 0)),
            in_mcast=_safe_int(line.get('rx_multicast', 0)),
            in_bcast=_safe_int(line.get('rx_broadcast', 0)),
            in_discards=_safe_int(line.get('rx_dropped', 0)),
            in_errors=_safe_int(line.get('rx_errors', 0)),
            out_octets=_safe_int(line.get('tx_bytes', 0)),
            out_ucast=_safe_int(line.get('tx_packets', 0)),
            out_mcast=_safe_int(line.get('tx_multicast', 0)),
            out_bcast=_safe_int(line.get('tx_broadcast', 0)),
            out_discards=_safe_int(line.get('tx_dropped', 0)),
            out_errors=_safe_int(line.get('tx_errors', 0)),
            jumbo=line.get('jumbo', False),
            satisfaction=_safe_int(line.get('satisfaction', 0)) if line.get('satisfaction') and line.get('up') else 0,
            port_poe=line.get('port_poe', False),
            poe_enable=line.get('poe_enable', False),
            poe_good=line.get('poe_good', False),
            poe_mode=line.get('poe_mode'),
            poe_current=float(line.get('poe_current', 0)),
            poe_voltage=float(line.get('poe_voltage', 0)),
            poe_power=float(line.get('poe_power', 0)),
            poe_class=line.get('poe_class'),
            dot1x_mode=line.get('dot1x_mode'),
            dot1x_status=line.get('dot1x_status'),
            ip_address=line.get('ip'),
            portconf=line.get('portconf'),
        )
        for idx, line in enumerate(section)
    ]


def discovery_unifi_network_port_if(  # fixme parsed_section_name
        params: Sequence[Mapping[str, Any]],
        section: Section,
) -> type_defs.DiscoveryResult:
    yield from interfaces.discover_interfaces(
        params,
        _convert_unifi_counters_if(section),
    )


def check_unifi_network_port_if(  # fixme parsed_section_name
        item: str,
        params: Mapping[str, Any],
        section: Section,
) -> type_defs.CheckResult:
    _converted_ifs = _convert_unifi_counters_if(section)
    yield from interfaces.check_multiple_interfaces(
        item,
        params,
        _converted_ifs,
    )


def inventory_unifi_network_ports(section):
    _total_ethernet_ports = 0
    _available_ethernet_ports = 0
    for idx, _iface in enumerate(section):
        _total_ethernet_ports += 1
        _available_ethernet_ports += 1 if _iface.oper_status == '2' else 0
        yield TableRow(
            path=["networking", "interfaces"],
            key_columns={"index": _safe_int(_iface.port_idx)},
            inventory_columns={
                "description": _iface.name,
                "alias": _iface.name,
                "speed": _safe_int(_iface.speed) * 1000000,
                "oper_status": _safe_int(_iface.oper_status),
                "admin_status": _safe_int(_iface.admin_status),
                "available": _iface.oper_status == '2',
                "vlans": _iface.portconf,
                "port_type": 6,
            }
        )

    yield Attributes(
        path=["networking"],
        inventory_attributes={
            "available_ethernet_ports": _available_ethernet_ports,
            "total_ethernet_ports": _total_ethernet_ports,
            "total_interfaces": _total_ethernet_ports
        }
    )


register.agent_section(
    name="unifi_device_if",
    parse_function=parse_unifi,
)

register.inventory_plugin(
    name="unifi_device_if",
    inventory_function=inventory_unifi_network_ports
)

register.check_plugin(
    name='unifi_device_if',
    sections=["unifi_device_if"],
    service_name='Interface %s',
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=register.RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    discovery_function=discovery_unifi_network_port_if,
    check_ruleset_name="if",
    check_default_parameters=interfaces.CHECK_DEFAULT_PARAMETERS,
    check_function=check_unifi_network_port_if,
)

# ***************************** UNIFI INTERFACE POE (Piggyback) *****************************

'''
'poe_caps': 7,
'poe_class': 'Class 4',
'poe_current': '151.12', mA
'poe_enable': True,
'poe_good': True,
'poe_mode': 'auto',
'poe_power': '8.02', W
'poe_voltage': '53.08', V

Class1: 12,95W/15,4W
Class2: 12,95W/15,4W
Class3: 12,95W/15,4W
Class4: 25,50W/30,0W
Class5: 40,00W/45,0W
Class6: 51,00W/60,0W
Class7: 62,00W/75,0W
Class8: 71,00W/90,0W
'''


def discovery_unifi_poe(
        params: Sequence[Mapping[str, Any]],
        section: Section,
) -> type_defs.DiscoveryResult:
    poe_ports = []
    for idx, line in enumerate(section):
        if 'poe_enable' in line:
            poe_ports.append(line)

    yield from interfaces.discover_interfaces(
        params,
        _convert_unifi_counters_if(poe_ports),
    )


def check_unifi_poe(
        item: str,
        params: Mapping[str, Any],
        section: Section,
) -> type_defs.CheckResult:
    _converted_ifs = _convert_unifi_counters_if(section)
    port = next(filter(
        lambda x: _safe_int(item, -1) == _safe_int(x.index) or item == x.alias or item == "%s %s" % (x.alias, x.index),
        _converted_ifs), None)  # fix Service Discovery appearance alias/descr
    if port:
        if port.port_poe:
            yield Result(state=State.OK, summary=f"POE: up" if port.poe_enable else 'POE: down')
            if port.poe_enable:
                if port.poe_good:
                    yield Result(state=State.OK, summary=f"Status: good")
                else:
                    yield Result(state=State.OK, summary=f"Status: bad")
                yield Result(state=State.OK, summary=f"mode: %s" % port.poe_mode)
                if port.poe_power > 0:
                    yield Result(state=State.OK, summary=f"class: %s" % port.poe_class)

                    yield from check_levels(
                        value=port.poe_voltage,
                        # levels_upper=params.get("voltage_level_upper"),
                        # levels_lower=params.get("voltage_level_lower"),
                        metric_name="voltage",
                        label=_("Voltage"),
                        render_func=lambda v: f"{v:.2f}V",  # pylint: disable=cell-var-from-loop,
                        boundaries=(190, 250),
                    )

                    yield from check_levels(
                        value=port.poe_current / 1000,
                        # levels_upper=params.get("current_level_upper"),
                        # levels_lower=params.get("current_level_lower"),
                        metric_name="current",
                        label=_("Current"),
                        render_func=lambda v: f"{v * 1000:.2f}mA",  # pylint: disable=cell-var-from-loop,
                        boundaries=(0, 1),
                        notice_only=False,
                    )

                    yield from check_levels(
                        value=port.poe_power,
                        # levels_upper=params.get("power_level_upper"),
                        # levels_lower=params.get("power_level_lower"),
                        metric_name="power",
                        label=_("Power"),
                        render_func=lambda v: f"{v:.2f}W",  # pylint: disable=cell-var-from-loop,
                        boundaries=(0, 100),
                        notice_only=False,
                    )


register.check_plugin(
    name="unifi_device_if_poe",
    sections=["unifi_device_if"],
    service_name="Interface %s POE",
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=register.RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    discovery_function=discovery_unifi_poe,
    check_function=check_unifi_poe,
    check_ruleset_name="if",
    check_default_parameters=interfaces.CHECK_DEFAULT_PARAMETERS,
)


# ***************************** UNIFI INTERFACE General Info (Piggyback) *****************************

def discovery_unifi_info(
        params: Sequence[Mapping[str, Any]],
        section: Section,
) -> type_defs.DiscoveryResult:
    yield from interfaces.discover_interfaces(
        params,
        _convert_unifi_counters_if(section),
    )


def check_unifi_info(
        item: str,
        params: Mapping[str, Any],
        section: Section,
) -> type_defs.CheckResult:
    _converted_ifs = _convert_unifi_counters_if(section)
    port = next(filter(
        lambda x: _safe_int(item, -1) == _safe_int(x.index) or item == x.alias or item == "%s %s" % (x.alias, x.index),
        _converted_ifs), None)  # fix Service Discovery appearance alias/descr
    if port:
        if port.portconf:
            yield Result(state=State.OK, summary=f"Network: {port.portconf}")
        if port.jumbo:
            yield Result(state=State.OK, summary=f"Jumbo-Frames: enabled")
        else:
            yield Result(state=State.OK, summary=f"Jumbo-Frames: disabled")
        yield Result(state=State.OK, summary=f"Satisfaction: {port.satisfaction}%%")
        yield Metric(name="satisfaction", value=max(0, port.satisfaction), boundaries=(0, 100))


register.check_plugin(
    name="unifi_device_if_info",
    sections=["unifi_device_if"],
    service_name="Interface %s Info",
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=register.RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    discovery_function=discovery_unifi_info,
    check_function=check_unifi_info,
    check_ruleset_name="if",
    check_default_parameters=interfaces.CHECK_DEFAULT_PARAMETERS,
)


# ***************************** UNIFI WIFI INTERFACE (Piggyback) *****************************

def discovery_unifi_wifi(section_unifi_device, section_unifi_device_users
                         ) -> type_defs.DiscoveryResult:
    wifi_ssid_data = section_unifi_device.get('vap_table')
    if wifi_ssid_data:
        for ssid in wifi_ssid_data:
            yield Service(item=f"%s_%s" % (ssid.get('radio_name'), ssid.get('essid')))


def check_unifi_wifi(item, section_unifi_device, section_unifi_device_users
                     ) -> type_defs.CheckResult:
    wifi_ssid_data = section_unifi_device.get('vap_table', [])
    for ssid in wifi_ssid_data:
        if item == f"%s_%s" % (ssid.get('radio_name'), ssid.get('essid')):
            yield Result(state=State.OK, summary=f"SSID: %s" % ssid.get('essid'))
            yield Result(state=State.OK, summary=f"State/Up: %s/%s" % (ssid.get('state'), ssid.get('up')))
            yield Result(state=State.OK, summary=f"Usage: %s" % ssid.get('usage'))
            yield Result(state=State.OK, summary=f"Interface: %s" % ssid.get('name'))
            yield Result(state=State.OK, summary=f"User: %s" % ssid.get('num_sta'))
            yield Metric("num_sta", int(ssid.get('num_sta', 0)))
            yield Result(state=State.OK, summary=f"avgClientSig: %sdBm" % ssid.get('avg_client_signal'))
            yield Metric("avg_client_signal", int(ssid.get('avg_client_signal', 0)))
            for user in section_unifi_device_users:
                if item == "%s_%s" % (user.get('radio_name'), user.get('essid')):
                    yield Result(state=State.OK,
                                 notice=f"Hostname: %s, MAC: %s, IP: %s, ESSID: %s, Network: %s, "
                                        f"RSSI: %sdBm, Noise: %sdBm, Signal: %sdBm" % (
                                            user.get('hostname'),
                                            user.get('mac'),
                                            user.get('ip'),
                                            user.get('essid'),
                                            user.get('network'),
                                            user.get('rssi'),
                                            user.get('noise'),
                                            user.get('signal'),
                                        )
                                 )
    else:
        if not wifi_ssid_data:
            yield Result(state=State.OK, summary=f"No Data available")


register.check_plugin(
    name="unifi_device_if_wifi",
    sections=["unifi_device", "unifi_device_users"],
    service_name="Unifi SSID %s",
    discovery_function=discovery_unifi_wifi,
    check_function=check_unifi_wifi,
)


# ***************************** UNIFI RADIO INTERFACE (Piggyback) *****************************

def wifi_type(ssid):
    if ssid.get('channel') < 15:
        return "2.4G"
    else:
        return "5G"


def discovery_unifi_radio(section_unifi_device, section_unifi_device_users
                          ) -> type_defs.DiscoveryResult:
    radio_data = section_unifi_device.get('radio_table')
    if radio_data:
        for radio in radio_data:
            yield Service(item=f"%s" % radio.get('name'))


def check_unifi_radio(item, section_unifi_device, section_unifi_device_users
                      ) -> type_defs.CheckResult:
    radio_data = section_unifi_device.get('radio_table')
    for idx, radio in enumerate(radio_data):
        if item == f"%s" % radio.get('name'):
            if len(section_unifi_device.get('radio_table_stats')) > 0:
                radio_stats = section_unifi_device.get('radio_table_stats')[idx]
                yield Result(state=State.OK, summary=f"State: %s" % radio_stats.get('state'))
                yield Result(state=State.OK, summary=f"Type: %s/%s" %
                                                     (wifi_type(radio_stats), radio_stats.get('radio')))
                yield Result(state=State.OK, summary=f"Channel: %s %s" %
                                                     (radio_stats.get('channel'),
                                                      "(fixed)" if radio.get('channel') else "(dynamic)"))
                yield Metric("channel", int(radio_stats.get('channel', 0)))
                yield Result(state=State.OK, summary=f"Width: %sMHz" % radio.get('ht'))
                if radio.get('antenna_gain'):
                    yield Result(state=State.OK, summary=f"Ant.Gain: %sdBm" % radio.get('antenna_gain'))
                yield Result(state=State.OK, summary=f"curr.AntGain: %sdBm" % radio.get('current_antenna_gain'))
                yield Result(state=State.OK, summary=f"User: %s" % radio_stats.get('user-num_sta'))
                yield Result(state=State.OK, summary=f"Guest: %s" % radio_stats.get('guest-num_sta'))
                yield Metric("user-num_sta", int(radio_stats.get('user-num_sta', 0)))
                yield Metric("guest-num_sta", int(radio_stats.get('guest-num_sta', 0)))

                yield Result(state=State.OK, summary=f"Satisfaction: %s%%" % radio_stats.get('satisfaction'))
                yield Metric("satisfaction", int(radio_stats.get('satisfaction', 0)))

                for user in section_unifi_device_users:
                    if user.get('radio_name') == item:
                        yield Result(state=State.OK, notice=f"Hostname: %s" % user.get('hostname'))
                        yield Result(state=State.OK, notice=f"MAC: %s" % user.get('mac'))
                        yield Result(state=State.OK, notice=f"IP: %s" % user.get('ip'))
                        yield Result(state=State.OK, notice=f"ESSID: %s" % user.get('essid'))
                        yield Result(state=State.OK, notice=f"Network: %s" % user.get('network'))
                        yield Result(state=State.OK, notice=f"RSSI: %s" % user.get('rssi'))
                        yield Result(state=State.OK, notice=f"Noise: %s" % user.get('noise'))
                        yield Result(state=State.OK, notice=f"Signal: %s" % user.get('signal'))
            else:
                yield Result(state=State.OK, summary=f"Wifi interface %s not available" % item)


register.agent_section(
    name="unifi_device_users",
    parse_function=parse_unifi,
)

register.check_plugin(
    name="unifi_device_radio",
    sections=["unifi_device", "unifi_device_users"],
    service_name="Unifi Radio %s",
    discovery_function=discovery_unifi_radio,
    check_function=check_unifi_radio,
)


# ***************************** UNIFI User (Piggyback) *****************************

def discover_unifi_user(
        params: Mapping[str, Any],
        section: Section,
) -> type_defs.DiscoveryResult:
    yield Service(item=f"Info")
    yield Service(item=f"Uplink")


def check_unifi_user(
        item: str,
        section: Section
) -> type_defs.CheckResult:
    if item == 'Info':
        yield Result(state=State.OK, summary=f"Hostname: %s" % section.get('hostname'))
        yield Result(state=State.OK, summary=f"Name: %s" % section.get('name'))
        yield Result(state=State.OK, summary=f"Note: %s" % section.get('note'))
        yield Result(state=State.OK, summary=f"Network: %s" % section.get('network'))
        yield Result(state=State.OK, summary=f"IP: %s" % section.get('ip'))
        yield Result(state=State.OK, summary=f"Static-DHCP: %s" % section.get('use_fixedip'))
        yield Result(state=State.OK, summary=f"Satifaction: %s%%" % section.get('satisfaction'))
        yield Result(state=State.OK, notice=f"OUI: %s" % section.get('oui'))
        yield Metric(name="satisfaction", value=int(section.get('satisfaction', 0)), boundaries=(0, 100))

    elif item == 'Uplink':
        if section.get('is_wired'):
            yield Result(state=State.OK, summary=f"Switch: %s" % section.get('uplink_name'))
            yield Result(state=State.OK, summary=f"Port: %s" % section.get('sw_port'))
            yield Result(state=State.OK, summary=f"Switch-MAC: %s" % section.get('sw_mac'))
        else:
            yield Result(state=State.OK, summary=f"Access-Point: %s" % section.get('uplink_name'))
            yield Result(state=State.OK, summary=f"Radio: %s" % section.get('radio_name'))
            yield Result(state=State.OK, summary=f"Channel: %s" % section.get('channel'))
            yield Result(state=State.OK, summary=f"Protocoll: %s" % section.get('radio_proto'))
            yield Result(state=State.OK, summary=f"ESSID: %s" % section.get('essid'))
            yield Result(state=State.OK, summary=f"AP-MAC: %s" % section.get('ap_mac'))
            yield Result(state=State.OK, notice=f"Signal: %sdBm" % int(section.get('signal', 0)))
            yield Result(state=State.OK, notice=f"Noise: %sdBm" % int(section.get('noise', 0)))
            yield Result(state=State.OK, notice=f"RSSI: %sdBm" % int(section.get('rssi', 0)))
            yield Result(state=State.OK, notice=f"RX-Rate: %sMbps" % int(section.get('rx_rate') / 1000))
            yield Result(state=State.OK, notice=f"TX-Rate: %sMBps" % int(section.get('tx_rate') / 1000))
            yield Metric(name="channel", value=int(section.get('channel', 0)))
            yield Metric(name="signal", value=int(section.get('signal', 0)), boundaries=(-120, 0), levels=(-70, -80))
            yield Metric(name="noise", value=int(section.get('noise', 0)), boundaries=(-120, 0), levels=(-90, -80))
            yield Metric(name="rssi", value=int(section.get('rssi', 0)) * -1, boundaries=(-120, 0))
            yield Metric(name="rx_rate", value=int(section.get('rx_rate') / 1000))
            yield Metric(name="tx_rate", value=int(section.get('tx_rate') / 1000))


register.agent_section(
    name="unifi_user",
    parse_function=parse_unifi,
)

register.check_plugin(
    name="unifi_user",
    sections=["unifi_user"],
    service_name="Unifi Client %s",
    discovery_function=discover_unifi_user,
    discovery_ruleset_name="unifi_user",
    discovery_default_parameters={},
    # discovery_ruleset_type=register.RuleSetType.ALL,
    # discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    check_function=check_unifi_user,
)
