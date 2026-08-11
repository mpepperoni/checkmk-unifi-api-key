#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from __future__ import annotations
import json
from typing import Any
from cmk.agent_based.v2 import AgentSection, StringTable
from pydantic import BaseModel, ConfigDict, Field, RootModel


class UnifiObject(BaseModel):
    """API object retaining fields not explicitly modelled by this extension."""

    model_config = ConfigDict(extra="allow")

    def value(
            self,
            name: str,
            default: Any = None,
    ) -> Any:
        return getattr(self, name, (self.model_extra or {}).get(name, default))


class UnifiController(UnifiObject):
    name: str | None = None
    ubnt_device_type: str | None = None
    build: str | None = None
    model: str | None = None
    type: str | None = None
    unsupported_device_count: int | None = None
    unsupported_device_list: list[str] | None = None


class UnifiSite(UnifiObject):
    name: str | None = None
    desc: str | None = None
    health: list[UnifiObject] = []
    num_new_alarms: int | None = None


class UnifiDevice(UnifiObject):
    name: str | None = None
    model: str | None = None
    type: str | None = None
    serial: str | None = None
    version: str | None = None
    ip: str | None = None
    state: int | str | None = None
    adopted: bool | None = None
    total_max_effective_power: float | None = None
    total_max_power: float | None = None
    total_used_power: float | None = None
    port_table: list[UnifiObject] = []
    vap_table: list[UnifiObject] = []
    radio_table: list[UnifiObject] = []
    radio_table_stats: list[UnifiObject] = []


class UnifiUser(UnifiObject):
    hostname: str | None = None
    name: str | None = None
    ip: str | None = None


class UnifiLastConnection(UnifiObject):
    connected: bool | None = None
    connected_at: int | None = None
    ip: str | None = None
    last_seen: int | None = None
    mac: str | None = None


class UnifiInterface(UnifiObject):
    """A physical UniFi switch port as exposed by the controller API."""

    aggregated_by: bool | None = None
    anomalies: int | None = None
    autoneg: bool | None = None
    bytes_rate: float | None = Field(default=None, alias="bytes-r")
    custom_anomalies: int | None = None
    enable: bool | None = None
    enabled: bool | None = None
    flowctrl_rx: bool | None = None
    flowctrl_tx: bool | None = None
    forward: str | None = None
    full_duplex: bool | None = None
    is_uplink: bool | None = None
    isolation: bool | None = None
    jumbo: bool | None = None
    last_connection: UnifiLastConnection | None = None
    link_down_count: int | None = None
    mac_table_count: int | None = None
    masked: bool | None = None
    media: str | None = None
    name: str = ""
    op_mode: str | None = None
    poe_caps: int | None = None
    poe_class: str | None = None
    poe_current: float | None = None
    poe_enable: bool | None = None
    poe_good: bool | None = None
    poe_mode: str | None = None
    poe_power: float | None = None
    poe_voltage: float | None = None
    port_idx: int
    port_poe: bool | None = None
    rx_broadcast: int | None = None
    rx_bytes: int | None = None
    rx_bytes_rate: float | None = Field(default=None, alias="rx_bytes-r")
    rx_dropped: int | None = None
    rx_errors: int | None = None
    rx_multicast: int | None = None
    rx_packets: int | None = None
    satisfaction: int | None = None
    satisfaction_reason: int | None = None
    speed: int | None = None
    speed_caps: int | None = None
    stp_edge_port: bool | None = None
    stp_pathcost: int | None = None
    stp_state: str | None = None
    tx_broadcast: int | None = None
    tx_bytes: int | None = None
    tx_bytes_rate: float | None = Field(default=None, alias="tx_bytes-r")
    tx_dropped: int | None = None
    tx_errors: int | None = None
    tx_multicast: int | None = None
    tx_packets: int | None = None
    up: bool | None = None


class UniFiInterfaces(RootModel[dict[str, UnifiInterface]]):
    pass


class UnifiSites(RootModel[list[UnifiSite]]):
    pass


class UniFiUsers(RootModel[list[UnifiUser]]):
    pass


DEVICE_STATES = {0: "disconnected", 1: "connected", 2: "pending"}


DEVICE_MODELS = {
    "UDM": "UDM", "UDMSE": "UDM-SE", "UDMPRO": "UDM-Pro", "UXGPRO": "UXG-Pro",
    "U7NHD": "UAP-nanoHD", "U6E": "U6-Enterprise", "UAL6": "U6-Lite",
    "UAP6": "U6-LR", "US8": "US-8", "US24": "US-24-G1", "US48": "US-48-G1",
    "USW24": "USW-24", "USW48": "USW-48", "USMINI": "USW-Flex-Mini",
}


def parse_json(
        string_table: StringTable,
) -> Any | None:
    if not string_table or not string_table[0]:
        return None
    try:
        return json.loads(string_table[0][0])
    except (IndexError, json.JSONDecodeError):
        return None


def parse_controller(
        string_table: StringTable,
) -> UnifiController | None:
    data = parse_json(string_table)
    return UnifiController.model_validate(data) if isinstance(data, dict) else None


def parse_sites(
        string_table: StringTable,
) -> UnifiSites | None:
    data = parse_json(string_table)
    return UnifiSites.model_validate(data) if isinstance(data, list) else None


def parse_device(
        string_table: StringTable,
) -> UnifiDevice | None:
    data = parse_json(string_table)
    return UnifiDevice.model_validate(data) if isinstance(data, dict) else None


def parse_interfaces(
        string_table: StringTable,
) -> UniFiInterfaces | None:
    data = parse_json(string_table)
    if not isinstance(data, list):
        return None
    interfaces = [UnifiInterface.model_validate(interface) for interface in data]
    return UniFiInterfaces({str(interface.port_idx): interface for interface in interfaces})


def parse_users(
        string_table: StringTable,
) -> UniFiUsers | None:
    data = parse_json(string_table)
    return UniFiUsers.model_validate(data) if isinstance(data, list) else None


def parse_user(
        string_table: StringTable,
) -> UnifiUser | None:
    data = parse_json(string_table)
    return UnifiUser.model_validate(data) if isinstance(data, dict) else None


def as_int(
        value: Any,
        default: int = 0,
) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(
        value: Any,
        default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def model_name(
        model: str | None,
) -> str:
    return DEVICE_MODELS.get(model or "", model or "unknown")


agent_section_unifi_controller = AgentSection(
    name="unifi_controller",
    parse_function=parse_controller,
)
agent_section_unifi_controller_sites = AgentSection(
    name="unifi_controller_sites",
    parse_function=parse_sites,
)
agent_section_unifi_site_controller_health = AgentSection(
    name="unifi_site_controller_health",
    parse_function=parse_sites,
)
agent_section_unifi_device = AgentSection(
    name="unifi_device",
    parse_function=parse_device,
)
agent_section_unifi_device_if = AgentSection(
    name="unifi_device_if",
    parse_function=parse_interfaces,
)
agent_section_unifi_device_users = AgentSection(
    name="unifi_device_users",
    parse_function=parse_users,
)
agent_section_unifi_site_users = AgentSection(
    name="unifi_site_users",
    parse_function=parse_users,
)
agent_section_unifi_user = AgentSection(
    name="unifi_user",
    parse_function=parse_user,
)
