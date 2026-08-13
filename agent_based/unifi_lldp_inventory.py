#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
"""Inventory LLDP neighbors reported by UniFi devices."""

from collections.abc import Mapping
from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow

from .unifi import DEVICE_MODELS, UniFiLldpNeighbors


def _system_description(model: str | None) -> str | None:
    """Format the model's descriptive and controller-internal names."""
    if not model:
        return None
    return (
        f"{long_name} ({model})"
        if (long_name := DEVICE_MODELS.get(model))
        else model
    )


def inventory_unifi_lldp_neighbors(
    params: Mapping[str, object], section: UniFiLldpNeighbors
) -> InventoryResult:
    """Store local LLDP links using Checkmk's standard LLDP table columns."""
    if not params.get("enable_lldp", True):
        return

    for neighbor in section.root:
        if neighbor.local_port_idx is None:
            continue
        yield TableRow(
            path=["networking", "lldp_neighbors"],
            key_columns={
                "neighbor_name": (
                    neighbor.remote_name or neighbor.chassis_id or "unknown"
                ),
                # Use the remote Uplink port number when UniFi provides one.
                # Otherwise retain the LLDP port identifier as the fallback.
                "neighbor_port": (
                    f"Port {neighbor.port_idx}"
                    if neighbor.port_idx is not None
                    else f"{neighbor.port_id}"
                    if neighbor.port_id
                    else "unknown"
                ),
                "local_port": (
                    f"Port {neighbor.local_port_idx}"
                    if neighbor.local_port_idx is not None
                    else neighbor.local_port_name or "null"
                ),
            },
            inventory_columns={
                **({"neighbor_address": neighbor.remote_ip} if neighbor.remote_ip else {}),
                **({"neighbor_id": neighbor.chassis_id} if neighbor.chassis_id else {}),
                **(
                    {"system_description": system_description}
                    if (system_description := _system_description(neighbor.remote_model))
                    else {}
                ),
                **(
                    {"port_description": neighbor.remote_port_name}
                    if neighbor.remote_port_name
                    else {"port_description": neighbor.port_id}
                    if neighbor.port_id
                    else {}
                ),
            },
            status_columns={},
        )


inventory_plugin_unifi_inf_lldp_neighbors = InventoryPlugin(
    name="unifi_inf_lldp_neighbors",
    sections=["unifi_device_lldp"],
    inventory_function=inventory_unifi_lldp_neighbors,
    inventory_default_parameters={"enable_interface": True, "enable_lldp": True},
    inventory_ruleset_name="unifi_inventory",
)
