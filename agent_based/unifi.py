#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, RootModel
import json
from cmk.agent_based.v2 import (
    AgentSection,
    HostLabel,
    HostLabelGenerator,
    StringTable
)


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


class UnifiRadio(UnifiObject):
    """A configured access-point radio returned by ``radio_table``.

    Ignore unknown controller fields so newly introduced UniFi properties do not
    prevent the complete device section from being parsed.
    """

    model_config = ConfigDict(extra="ignore")

    antenna_gain: int | None = None
    antenna_id: int | None = None
    builtin_ant_gain: int | None = None
    builtin_antenna: bool | None = None
    channel: int | str | None = None
    current_antenna_gain: int | None = None
    hard_noise_floor_enabled: bool | None = None
    has_dfs: bool | None = None
    has_fccdfs: bool | None = None
    has_ht160: bool | None = None
    ht: int | None = None
    is_11ac: bool | None = None
    is_11ax: bool | None = None
    loadbalance_enabled: bool | None = None
    max_txpower: int | None = None
    min_rssi: int | None = None
    min_rssi_enabled: bool | None = None
    min_txpower: int | None = None
    name: str | None = None
    nss: int | None = None
    radio: str | None = None
    radio_caps: int | None = None
    radio_caps2: int | None = None
    sens_level_enabled: bool | None = None
    tx_power: int | None = None
    tx_power_mode: str | None = None
    vwire_enabled: bool | None = None


class UnifiVap(UnifiObject):
    """A virtual access point returned by ``vap_table``.

    Nested controller structures intentionally remain dictionaries. Their
    schema varies between controller and firmware versions and is not needed by
    the inventory tables.
    """

    model_config = ConfigDict(extra="ignore")

    anomalies_bar_chart: dict[str, int] | None = None
    anomalies_bar_chart_now: dict[str, int] | None = None
    ap_mac: str | None = None
    avg_client_signal: int | None = None
    bssid: str | None = None
    bw: int | None = None
    ccq: int | None = None
    channel: int | None = None
    dns_avg_latency: int | None = None
    essid: str | None = None
    extchannel: int | None = None
    icmp_avg_rtt: int | None = None
    id: str | None = None
    is_guest: bool | None = None
    is_wep: bool | None = None
    mac_filter_rejections: int | None = None
    name: str | None = None
    num_satisfaction_sta: int | None = None
    num_sta: int | None = None
    radio: str | None = None
    radio_name: str | None = None
    reasons_bar_chart: dict[str, int] | None = None
    reasons_bar_chart_now: dict[str, int] | None = None
    rx_bcast: int | None = None
    rx_bytes: int | None = None
    rx_crypts: int | None = None
    rx_dropped: int | None = None
    rx_errors: int | None = None
    rx_frags: int | None = None
    rx_mcast: int | None = None
    rx_nwids: int | None = None
    rx_packets: int | None = None
    rx_tcp_stats: dict[str, int] | None = None
    satisfaction: int | None = None
    site_id: str | None = None
    state: str | None = None
    t: str | None = None
    tx_bcast: int | None = None
    tx_bytes: int | None = None
    tx_combined_retries: int | None = None
    tx_data_mpdu_bytes: int | None = None
    tx_dropped: int | None = None
    tx_errors: int | None = None
    tx_mcast: int | None = None
    tx_packets: int | None = None
    tx_power: int | None = None
    tx_retries: int | None = None
    tx_rts_retries: int | None = None
    tx_success: int | None = None
    tx_tcp_stats: dict[str, int] | None = None
    tx_total: int | None = None
    up: bool | None = None
    usage: str | None = None
    wifi_tx_attempts: int | None = None
    wifi_tx_dropped: int | None = None
    wifi_tx_latency_mov: dict[str, int] | None = None
    wlanconf_id: str | None = None


class UnifiRadioStatistics(UnifiObject):
    """The current operational values returned by ``radio_table_stats``."""

    model_config = ConfigDict(extra="ignore")

    ast_be_xmit: int | None = None
    ast_cst: int | None = None
    ast_txto: int | None = None
    bw: int | None = None
    channel: int | None = None
    cu_self_rx: int | None = None
    cu_self_tx: int | None = None
    cu_total: int | None = None
    extchannel: int | None = None
    gain: int | None = None
    guest_num_sta: int | None = Field(default=None, alias="guest-num_sta")
    last_channel: int | None = None
    name: str | None = None
    num_sta: int | None = None
    radio: str | None = None
    satisfaction: int | None = None
    state: str | None = None
    tx_packets: int | None = None
    tx_power: int | None = None
    tx_retries: int | None = None
    tx_retries_pct: float | None = None
    user_num_sta: int | None = Field(default=None, alias="user-num_sta")


class UnifiLldpNeighbor(UnifiObject):
    """An LLDP neighbor reported by the UniFi controller.

    The controller returns this structure in a device's ``lldp_table``.  The
    special agent also attaches the same object to the corresponding local
    interface, allowing both sections to use one schema.
    """

    chassis_id: str | None = None
    chassis_id_subtype: str | None = None
    is_wired: bool | None = None
    local_port_idx: int | None = None
    local_port_name: str | None = None
    port_id: str | None = None
    power_allocated: int | None = None
    power_requested: int | None = None
    remote_name: str | None = None
    remote_model: str | None = None
    remote_ip: str | None = None
    remote_type: str | None = None


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
    lldp_table: list[UnifiLldpNeighbor] = Field(default_factory=list)
    port_table: list[UnifiObject] = []
    vap_table: list[UnifiVap] = []
    radio_table: list[UnifiRadio] = []
    radio_table_stats: list[UnifiRadioStatistics] = []


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

    # UniFi uses ``false`` for a regular port and the parent port number for a
    # member of a link aggregation group.
    aggregated_by: bool | int | None = None
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
    lldp_neighbors: list[UnifiLldpNeighbor] = Field(default_factory=list)
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


class UniFiLldpNeighbors(RootModel[list[UnifiLldpNeighbor]]):
    pass


class UnifiSites(RootModel[list[UnifiSite]]):
    pass


class UniFiUsers(RootModel[list[UnifiUser]]):
    pass


DEVICE_STATES = {0: "disconnected", 1: "connected", 2: "pending"}
DEVICE_STATE_NUMBERS = {name: number for number, name in DEVICE_STATES.items()}

# UniFi's radio field identifies the frequency band independently from the
# configured channel. Keep this mapping shared by checks and inventory UIs.
RADIO_BANDS = {
    "ng": "2.4 GHz",
    "na": "5 GHz",
    "6e": "6 GHz",
}


DEVICE_MODELS = {
    "UDM": "UDM",
    "UDMSE": "UDM-SE",
    "UDMPRO": "UDM-Pro",
    "UXGPRO": "UXG-Pro",
    "U7NHD": "UAP-nanoHD",
    "U6E": "U6-Enterprise",
    "UAL6": "U6-Lite",
    "UAP6": "U6-LR",
    "U6ENT": "U6-Enterprise",
    "U6ENTIW": "U6-Enterprise-IW",
    "U6EXT": "U6-Extender",
    "U6IW": "U6-In-Wall",
    "U6M": "U6-Mesh",
    "UAP6MP": "U6-Pro",
    "UAPL6": "U6+",
    "U7PRO": "U7-Pro",
    "U7ENT": "U7-Enterprise",
    "G7LR": "U7-LR",
    "U7LT": "UAP-AC-Lite",
    "U7LR": "UAP-AC-LR",
    "U7PG2": "UAP-AC-Pro",
    "U7HD": "UAP-AC-HD",
    "U7SHD": "UAP-AC-SHD",
    "U7MSH": "UAP-AC-Mesh",
    "U7MP": "UAP-AC-Mesh-Pro",
    "U7P": "UAP-Pro",
    "U7EDU": "UAP-AC-EDU",
    "U7Ev2": "UAP-AC",
    "U7O": "UAP-AC-Outdoor",
    "U2S48": "UAP",
    "U2Sv2": "UAP",
    "U5O": "UAP-Outdoor5",
    "US8": "US-8",
    "US24": "US-24-G1",
    "US48": "US-48-G1",
    "USW24": "USW-24",
    "USW48": "USW-48",
    "USMINI": "USW-Flex-Mini",
    "US6XG150": "US-XG-6PoE",
    "USL8LP": "USW-Lite-8-PoE",
    "USL8LPB": "USW-Lite-8-PoE",
    "USL8MP": "USW-Mission-Critical",
    "USL8A": "USW-Aggregation",
    "USL16P": "USW-16-PoE",
    "USL16LP": "USW-Lite-16-PoE",
    "USL24": "USW-24",
    "USL24P": "USW-24-PoE",
    "USL48": "USW-48",
    "USL48P": "USW-48-PoE",
    "US24PRO": "USW-Pro-24-PoE",
    "US24PRO2": "USW-Pro-24",
    "US48PRO": "USW-Pro-48-PoE",
    "US48PRO2": "USW-Pro-48",
    "US68P": "USW-Enterprise-8-PoE",
    "US624P": "USW-Enterprise-24-PoE",
    "US648P": "USW-Enterprise-48-PoE",
    "USXG24": "USW-Enterprise-XG-24",
    "USAGGPRO": "USW-Pro-Aggregation",
    "USPM24P": "USW-Pro-Max-24-PoE",
    "USPM48P": "USW-Pro-Max-48-PoE",
    "USMINI2": "USW-Flex-Mini",
    "USXG": "US-16-XG",
    "UX": "UniFi-Express",
    "UGW3": "USG-3P",
    "UGW4": "USG-Pro-4",
    "UGWHD4": "USG",
    "UGWXG": "USG-XG-8",
    "USPPDUP": "USP-PDU-Pro",
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


def parse_lldp_neighbors(
        string_table: StringTable,
) -> UniFiLldpNeighbors | None:
    data = parse_json(string_table)
    return UniFiLldpNeighbors.model_validate(data) if isinstance(data, list) else None


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


def device_state(
        value: int | str | None,
) -> str:
    """Return a normalized UniFi device state.

    Most controller versions use the numeric values 0, 1, and 2.  Some API
    versions return their textual equivalents instead, so accepting both keeps
    a connected device from being reported as an unknown critical state.
    """
    if isinstance(value, str):
        normalized = value.lower()
        if normalized in DEVICE_STATE_NUMBERS:
            return normalized
    return DEVICE_STATES.get(as_int(value, -1), "unknown")


def model_name(
        model: str | None,
) -> str:
    return DEVICE_MODELS.get(model or "", model or "unknown")


def host_labels_unifi_device(
        section: UnifiDevice,
) -> HostLabelGenerator:
    """Expose the UniFi model and the API-provided generic device type."""
    if section.model:
        yield HostLabel("cmk/unifi_device_model", section.model)
    if section.type:
        yield HostLabel("cmk/unifi_device_type", section.type)


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
    host_label_function=host_labels_unifi_device,
)
agent_section_unifi_device_if = AgentSection(
    name="unifi_device_if",
    parse_function=parse_interfaces,
)
agent_section_unifi_device_lldp = AgentSection(
    name="unifi_device_lldp",
    parse_function=parse_lldp_neighbors,
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
