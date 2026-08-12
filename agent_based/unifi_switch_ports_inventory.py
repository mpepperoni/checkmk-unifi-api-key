#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
"""Inventory UniFi-specific switch port configuration and capabilities."""

from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow

from .unifi import UniFiInterfaces, UnifiInterface


def _port_inventory_columns(port: UnifiInterface) -> dict[str, object]:
    """Return non-counter port properties not represented by the standard table."""
    columns: dict[str, object] = {
        "name": port.name,
        **({"media": port.media} if port.media else {}),
        **({"operating_mode": port.op_mode} if port.op_mode else {}),
        **({"autonegotiation": port.autoneg} if port.autoneg is not None else {}),
        **({"flow_control_rx": port.flowctrl_rx} if port.flowctrl_rx is not None else {}),
        **({"flow_control_tx": port.flowctrl_tx} if port.flowctrl_tx is not None else {}),
        **({"speed_capabilities": port.speed_caps} if port.speed_caps is not None else {}),
        **({"forwarding_mode": port.forward} if port.forward else {}),
        **({"is_uplink": port.is_uplink} if port.is_uplink is not None else {}),
        **({"aggregated": port.aggregated_by} if port.aggregated_by is not None else {}),
        **({"isolated": port.isolation} if port.isolation is not None else {}),
        **({"jumbo_frames": port.jumbo} if port.jumbo is not None else {}),
        **({"masked": port.masked} if port.masked is not None else {}),
        **({"stp_state": port.stp_state} if port.stp_state else {}),
        **({"stp_path_cost": port.stp_pathcost} if port.stp_pathcost is not None else {}),
        **({"stp_edge_port": port.stp_edge_port} if port.stp_edge_port is not None else {}),
        **({"poe_capable": port.port_poe} if port.port_poe is not None else {}),
        **({"poe_capabilities": port.poe_caps} if port.poe_caps is not None else {}),
        **({"poe_enabled": port.poe_enable} if port.poe_enable is not None else {}),
        **({"poe_mode": port.poe_mode} if port.poe_mode else {}),
        **({"poe_class": port.poe_class} if port.poe_class else {}),
        **({"poe_good": port.poe_good} if port.poe_good is not None else {}),
    }

    # These fields are not available on all UniFi controller and switch versions.
    for source, destination in (
        ("native_networkconf_id", "native_network_id"),
        ("voice_networkconf_id", "voice_network_id"),
        ("tagged_vlan_mgmt", "tagged_vlan_management"),
        ("dot1x_mode", "dot1x_mode"),
        ("dot1x_status", "dot1x_status"),
        ("lldpmed_enabled", "lldp_med_enabled"),
        ("setting_preference", "setting_preference"),
        ("port_security_enabled", "port_security_enabled"),
    ):
        value = port.value(source)
        if value is not None:
            columns[destination] = value

    return columns


def inventory_unifi_switch_ports(section: UniFiInterfaces) -> InventoryResult:
    """Store UniFi-specific port properties that have no standard IF-MIB equivalent."""
    for port in section.root.values():
        yield TableRow(
            path=["networking", "unifi_switch_ports"],
            key_columns={"index": port.port_idx},
            inventory_columns=_port_inventory_columns(port),
            status_columns={
                key: value
                for key, value in {
                    "mac_table_count": port.mac_table_count,
                    "link_down_count": port.link_down_count,
                    "satisfaction": port.satisfaction,
                }.items()
                if value is not None
            },
        )


inventory_plugin_unifi_inf_switch_ports = InventoryPlugin(
    name="unifi_inf_switch_ports",
    sections=["unifi_device_if"],
    inventory_function=inventory_unifi_switch_ports,
)
