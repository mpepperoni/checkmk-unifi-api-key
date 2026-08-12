#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from __future__ import annotations
from typing import Any
from cmk.agent_based.v2 import InventoryPlugin, InventoryResult, TableRow
from .unifi import UnifiDevice, UnifiObject


def _integer(
        value: Any
) -> int | None:
    """Return controller numbers as integers but never invent a value."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _present_values(
        values: dict[str, Any]
) -> dict[str, Any]:
    """Inventory API table columns must not contain unavailable values."""
    return {name: value for name, value in values.items() if value is not None}


def _radio_columns(
        radio: UnifiObject,
        statistics: UnifiObject | None
) -> dict[str, Any]:
    """Build one radio row, preferring the active channel reported in stats."""
    return _present_values(
        {
            "antenna_gain": _integer(radio.value("antenna_gain")),
            "builtin_ant_gain": _integer(radio.value("builtin_ant_gain")),
            "builtin_antenna": radio.value("builtin_antenna"),
            "channel": _integer(
                statistics.value("channel", radio.value("channel"))
                if statistics is not None
                else radio.value("channel")
            ),
            "hard_noise_floor_enabled": radio.value("hard_noise_floor_enabled"),
            "ht": _integer(radio.value("ht")),
            "max_txpower": _integer(radio.value("max_txpower")),
            "min_rssi_enabled": radio.value("min_rssi_enabled"),
            "min_txpower": _integer(radio.value("min_txpower")),
            "name": radio.value("name"),
            "nss": _integer(radio.value("nss")),
            "radio": radio.value("radio"),
            "sens_level_enabled": radio.value("sens_level_enabled"),
            "tx_power": _integer(radio.value("tx_power")),
            "tx_power_mode": radio.value("tx_power_mode"),
            "vwire_enabled": radio.value("vwire_enabled"),
        }
    )


def _vap_columns(
        vap: UnifiObject
) -> dict[str, Any]:
    return _present_values(
        {
            "essid": vap.value("essid"),
            "bssid": vap.value("bssid"),
            "ap_mac": vap.value("ap_mac"),
            "channel": _integer(vap.value("channel")),
            "name": vap.value("name"),
            "radio": vap.value("radio"),
            "radio_name": vap.value("radio_name"),
            "bw": _integer(vap.value("bw")),
        }
    )


def inventory_unifi_wifi(
        section: UnifiDevice
) -> InventoryResult:
    """Expose UniFi radio configuration and VAP assignments in inventory."""
    statistics_by_name = {
        str(statistics.value("name")): statistics
        for statistics in section.radio_table_stats
        if statistics.value("name") is not None
    }

    for index, radio in enumerate(section.radio_table):
        name = radio.value("name")
        statistics = statistics_by_name.get(str(name)) if name is not None else None
        yield TableRow(
            path=["networking", "unifi_wifi_radios"],
            key_columns={"index": index},
            inventory_columns=_radio_columns(radio, statistics),
        )

    for index, vap in enumerate(section.vap_table):
        yield TableRow(
            path=["networking", "unifi_wifi_vaps"],
            key_columns={"index": index},
            inventory_columns=_vap_columns(vap),
        )


inventory_plugin_unifi_wifi_inventory = InventoryPlugin(
    name="unifi_wifi_inventory",
    sections=["unifi_device"],
    inventory_function=inventory_unifi_wifi,
)
