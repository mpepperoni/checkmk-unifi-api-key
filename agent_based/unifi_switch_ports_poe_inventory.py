#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow
from .unifi import UniFiInterfaces, UnifiInterface


def _poe_capabilities(value: int) -> str:
    """Render the UniFi PoE capability bit mask without exposing 0 or 1 alone."""
    if value == 0:
        return "Not supported"
    return f"Supported (capability mask: {value})"


def _poe_inventory_columns(port: UnifiInterface) -> dict[str, object]:
    columns: dict[str, object] = {
        "descr": f"Port {port.port_idx}",
        "alias": port.name,
    }
    if port.port_poe is not None:
        columns["poe_capable"] = "Capable" if port.port_poe else "Not capable"
    if port.poe_caps is not None:
        columns["poe_capabilities"] = _poe_capabilities(port.poe_caps)
    if port.poe_enable is not None:
        columns["poe_enabled"] = "Enabled" if port.poe_enable else "Disabled"
    if port.poe_mode:
        columns["poe_mode"] = port.poe_mode
    if port.poe_class:
        columns["poe_class"] = port.poe_class
    return columns


def inventory_unifi_switch_ports_poe(section: UniFiInterfaces) -> InventoryResult:
    """Store the PoE configuration reported for each UniFi switch port."""
    for port in section.root.values():
        yield TableRow(
            path=["networking", "interfaces_poe"],
            key_columns={"index": str(port.port_idx)},
            inventory_columns=_poe_inventory_columns(port),
        )


inventory_plugin_unifi_inf_switch_ports_poe = InventoryPlugin(
    name="unifi_inf_switch_ports_poe",
    sections=["unifi_device_if"],
    inventory_function=inventory_unifi_switch_ports_poe,
)
