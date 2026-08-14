#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from collections.abc import Mapping
from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow
from cmk.plugins.lib.inventory_interfaces import Interface, inventorize_interfaces
from .unifi import UniFiInterfaces, interface_type


def _admin_status(port_enabled: bool | None) -> int | None:
    if port_enabled is None:
        return None
    return 1 if port_enabled else 2


def _duplex(full_duplex: bool | None, port_up: bool | None) -> str:
    if not port_up:
        return ""
    if full_duplex is True:
        return "full"
    if full_duplex is False:
        return "half"
    return ""


def inventory_unifi_interfaces(
    params: Mapping[str, object], section: UniFiInterfaces
) -> InventoryResult:
    """Expose UniFi ports and virtual interfaces like standard SNMP interfaces."""
    if not params.get("enable_interface", True):
        return

    interfaces = [
        Interface(
            index=str(port.port_idx),
            descr=f"Port {port.port_idx}",
            alias=port.name,
            type=interface_type(port),
            speed=(port.speed or 0) * 1_000_000,
            oper_status=1 if port.up else 2,
            # UniFi does not provide the switch port's own physical MAC address.
            phys_address="",
            admin_status=_admin_status(
                port.enabled if port.enabled is not None else port.enable
            ),
        )
        for port in section.root.values()
    ]
    yield from inventorize_interfaces(
        {},
        interfaces,
        n_total=len(interfaces),
    )

    # The duplex column is displayed by the Checkmk 2.5 inventory UI. Older
    # Checkmk versions ignore the unknown column, so retain it for forward
    # compatibility rather than putting this standard interface property into the
    # UniFi-specific switch-port inventory.
    for port in section.root.values():
        yield TableRow(
            path=["networking", "interfaces"],
            key_columns={"index": port.port_idx},
            inventory_columns={"duplex": _duplex(port.full_duplex, port.up)},
        )


inventory_plugin_unifi_inf_interfaces = InventoryPlugin(
    name="unifi_inf_interfaces",
    sections=["unifi_device_if"],
    inventory_function=inventory_unifi_interfaces,
    inventory_default_parameters={"enable_interface": True, "enable_lldp": True},
    inventory_ruleset_name="unifi_inventory",
)
