#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
"""Inventory general hardware and firmware data of a UniFi device."""

from cmk.agent_based.v2 import Attributes, InventoryPlugin, InventoryResult

from .unifi import UnifiDevice, model_name


def inventory_unifi_device(section: UnifiDevice) -> InventoryResult:
    """Store UniFi device properties in Checkmk's standard inventory paths."""
    yield Attributes(
        path=["hardware", "system"],
        inventory_attributes={
            "manufacturer": "Ubiquiti",
            **({"product": model_name(section.model)} if section.model else {}),
            **({"model": section.model} if section.model else {}),
            **({"serial": section.serial} if section.serial else {}),
            **({"node_name": section.name} if section.name else {}),
            **({"description": section.type} if section.type else {}),
        },
    )

    if section.version or section.type:
        yield Attributes(
            path=["software", "os"],
            inventory_attributes={
                "vendor": "Ubiquiti",
                "name": "UniFi Network device firmware",
                **({"version": section.version} if section.version else {}),
                **({"type": section.type} if section.type else {}),
            },
        )

    configuration = {
        **({"management_ip": section.ip} if section.ip else {}),
        **({"adopted": section.adopted} if section.adopted is not None else {}),
        **({"state": section.state} if section.state is not None else {}),
    }
    if configuration:
        yield Attributes(
            path=["software", "configuration", "unifi_device"],
            inventory_attributes=configuration,
        )


inventory_plugin_unifi_inf_device = InventoryPlugin(
    name="unifi_inf_device",
    sections=["unifi_device"],
    inventory_function=inventory_unifi_device,
)
