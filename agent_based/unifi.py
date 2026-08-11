"""Shared data models and parsers for the UniFi special agent."""

from __future__ import annotations

import json
from typing import Any

from cmk.agent_based.v2 import AgentSection, StringTable
from pydantic import BaseModel, ConfigDict, RootModel


class UniFiObject(BaseModel):
    """API object retaining fields not explicitly modelled by this extension."""

    model_config = ConfigDict(extra="allow")

    def value(self, name: str, default: Any = None) -> Any:
        return getattr(self, name, (self.model_extra or {}).get(name, default))


class UniFiController(UniFiObject):
    name: str | None = None
    ubnt_device_type: str | None = None
    build: str | None = None
    model: str | None = None
    type: str | None = None
    unsupported_device_count: int | None = None
    unsupported_device_list: list[str] | None = None


class UniFiSite(UniFiObject):
    name: str | None = None
    desc: str | None = None
    health: list[UniFiObject] = []
    num_new_alarms: int | None = None


class UniFiDevice(UniFiObject):
    name: str | None = None
    model: str | None = None
    type: str | None = None
    serial: str | None = None
    version: str | None = None
    ip: str | None = None
    state: int | str | None = None
    adopted: bool | None = None
    port_table: list[UniFiObject] = []
    vap_table: list[UniFiObject] = []
    radio_table: list[UniFiObject] = []
    radio_table_stats: list[UniFiObject] = []


class UniFiUser(UniFiObject):
    hostname: str | None = None
    name: str | None = None
    ip: str | None = None


class UniFiInterfaces(RootModel[list[UniFiObject]]):
    pass


class UniFiSites(RootModel[list[UniFiSite]]):
    pass


class UniFiUsers(RootModel[list[UniFiUser]]):
    pass


DEVICE_STATES = {0: "disconnected", 1: "connected", 2: "pending"}


DEVICE_MODELS = {
    "UDM": "UDM", "UDMSE": "UDM-SE", "UDMPRO": "UDM-Pro", "UXGPRO": "UXG-Pro",
    "U7NHD": "UAP-nanoHD", "U6E": "U6-Enterprise", "UAL6": "U6-Lite",
    "UAP6": "U6-LR", "US8": "US-8", "US24": "US-24-G1", "US48": "US-48-G1",
    "USW24": "USW-24", "USW48": "USW-48", "USMINI": "USW-Flex-Mini",
}


def parse_json(string_table: StringTable) -> Any | None:
    if not string_table or not string_table[0]:
        return None
    try:
        return json.loads(string_table[0][0])
    except (IndexError, json.JSONDecodeError):
        return None


def parse_controller(string_table: StringTable) -> UniFiController | None:
    data = parse_json(string_table)
    return UniFiController.model_validate(data) if isinstance(data, dict) else None


def parse_sites(string_table: StringTable) -> UniFiSites | None:
    data = parse_json(string_table)
    return UniFiSites.model_validate(data) if isinstance(data, list) else None


def parse_device(string_table: StringTable) -> UniFiDevice | None:
    data = parse_json(string_table)
    return UniFiDevice.model_validate(data) if isinstance(data, dict) else None


def parse_interfaces(string_table: StringTable) -> UniFiInterfaces | None:
    data = parse_json(string_table)
    return UniFiInterfaces.model_validate(data) if isinstance(data, list) else None


def parse_users(string_table: StringTable) -> UniFiUsers | None:
    data = parse_json(string_table)
    return UniFiUsers.model_validate(data) if isinstance(data, list) else None


def parse_user(string_table: StringTable) -> UniFiUser | None:
    data = parse_json(string_table)
    return UniFiUser.model_validate(data) if isinstance(data, dict) else None


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def model_name(model: str | None) -> str:
    return DEVICE_MODELS.get(model or "", model or "unknown")


agent_section_unifi_controller = AgentSection(name="unifi_controller", parse_function=parse_controller)
agent_section_unifi_controller_sites = AgentSection(name="unifi_controller_sites", parse_function=parse_sites)
agent_section_unifi_site_controller_health = AgentSection(name="unifi_site_controller_health", parse_function=parse_sites)
agent_section_unifi_device = AgentSection(name="unifi_device", parse_function=parse_device)
agent_section_unifi_device_if = AgentSection(name="unifi_device_if", parse_function=parse_interfaces)
agent_section_unifi_device_users = AgentSection(name="unifi_device_users", parse_function=parse_users)
agent_section_unifi_site_users = AgentSection(name="unifi_site_users", parse_function=parse_users)
agent_section_unifi_user = AgentSection(name="unifi_user", parse_function=parse_user)
