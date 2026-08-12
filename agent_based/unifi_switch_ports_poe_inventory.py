#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from collections.abc import Mapping

from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow
from .unifi import UniFiInterfaces, UnifiInterface

poe_capable_mapping = {
    False: "No",
    True: "Yes",
}

poe_enabled_mapping = {
    False: "No",
    True: "Yes",
}

poe_class_mapping = {
    "Unknown": "",
    "Class 0": "Class 0",
    "Class 1": "Class 1",
    "Class 2": "Class 2",
    "Class 3": "Class 3",
    "Class 4": "Class 4",
    "Class 5": "Class 5",
    "Class 6": "Class 6",
    "Class 7": "Class 7",
    "Class 8": "Class 8",
}

poe_mode_mapping = {
    "off": "Off",
    "auto": "Auto",
    "pasv24": "24V Passive",
    "passthrough": "Passthrough",
}

poe_capabilities_mapping = {
    0: "Not supported",
    1: "Supported (capability mask: 1)",
    3: "Supported (capability mask: 3)",
    7: "Supported (capability mask: 7)",
}


def _mapped_value(value: object, mapping: Mapping[object, str]) -> str:
    """Return the raw API value if the controller reports an unknown setting."""
    return mapping.get(value, str(value))


def _poe_capabilities(value: int) -> str:
    """Render known UniFi PoE capability masks with a readable fallback."""
    return _mapped_value(value, poe_capabilities_mapping)


def _poe_inventory_columns(port: UnifiInterface) -> dict[str, object]:
    columns: dict[str, object] = {
        "descr": f"Port {port.port_idx}",
        "alias": port.name,
    }
    if port.port_poe is not None:
        columns["poe_capable"] = _mapped_value(port.port_poe, poe_capable_mapping)
    if port.poe_caps is not None:
        columns["poe_capabilities"] = _poe_capabilities(port.poe_caps)
    if port.poe_enable is not None:
        columns["poe_enabled"] = _mapped_value(port.poe_enable, poe_enabled_mapping)
    if port.poe_mode:
        columns["poe_mode"] = _mapped_value(port.poe_mode, poe_mode_mapping)
    if port.poe_class:
        columns["poe_class"] = _mapped_value(port.poe_class, poe_class_mapping)
    return columns


def inventory_unifi_switch_ports_poe(section: UniFiInterfaces) -> InventoryResult:
    """Store the PoE configuration reported for each UniFi switch port."""
    for port in section.root.values():
        yield TableRow(
            path=["networking", "unifi_interfaces_poe"],
            key_columns={"index": str(port.port_idx)},
            inventory_columns=_poe_inventory_columns(port),
        )


inventory_plugin_unifi_inf_switch_ports_poe = InventoryPlugin(
    name="unifi_inf_switch_ports_poe",
    sections=["unifi_device_if"],
    inventory_function=inventory_unifi_switch_ports_poe,
)
