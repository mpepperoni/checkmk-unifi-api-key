#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
"""Checkmk inventory UI definitions for UniFi Wi-Fi radios and VAPs."""

from cmk.inventory_ui.v1_unstable import (
    BoolField,
    ChoiceField,
    DecimalNotation,
    Node,
    NumberField,
    StrictPrecision,
    Table,
    TextField,
    Title,
    Unit,
    View,
)
from cmk_addons.plugins.unifi.agent_based.unifi import RADIO_BANDS


def _integer(title: str, unit: str = "") -> NumberField:
    return NumberField(
        Title(title),
        render=Unit(DecimalNotation(unit), StrictPrecision(0)),
    )


_RADIO_BANDS = {identifier: f"{band} ({identifier})" for identifier, band in RADIO_BANDS.items()}

_TX_POWER_MODES = {
    "auto": "Automatic",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "custom": "Custom",
}


node_networking_unifi_wifi_radios = Node(
    name="networking_unifi_wifi_radios",
    path=["networking", "unifi_wifi_radios"],
    title=Title("UniFi Wi-Fi Radios"),
    table=Table(
        view=View(name="invunifiwifiradios", title=Title("UniFi Wi-Fi Radios")),
        columns={
            "index": _integer("Index"),
            # ``radio_table.name`` is UniFi's radio identifier (for example
            # ``ra0``). VAP rows refer to this exact value via ``radio_name``.
            "name": TextField(Title("Radio identifier")),
            "radio": ChoiceField(Title("Frequency band"), mapping=_RADIO_BANDS),
            "channel": _integer("Channel"),
            "ht": _integer("Channel width", "MHz"),
            "nss": _integer("Spatial streams"),
            "antenna_gain": _integer("Antenna gain", "dBi"),
            "builtin_ant_gain": _integer("Built-in antenna gain", "dBi"),
            "builtin_antenna": BoolField(Title("Built-in antenna")),
            "hard_noise_floor_enabled": BoolField(Title("Hard noise floor enabled")),
            "min_rssi_enabled": BoolField(Title("Minimum RSSI enabled")),
            "sens_level_enabled": BoolField(Title("Sensitivity level enabled")),
            "vwire_enabled": BoolField(Title("Virtual wire enabled")),
            "min_txpower": _integer("Minimum TX power", "dBm"),
            "max_txpower": _integer("Maximum TX power", "dBm"),
            "tx_power": _integer("TX power", "dBm"),
            "tx_power_mode": ChoiceField(Title("TX power mode"), mapping=_TX_POWER_MODES),
        },
    ),
)


node_networking_unifi_wifi_vaps = Node(
    name="networking_unifi_wifi_vaps",
    path=["networking", "unifi_wifi_vaps"],
    title=Title("UniFi Wi-Fi Virtual Access Points"),
    table=Table(
        view=View(name="invunifiwifivaps", title=Title("UniFi Wi-Fi VAPs")),
        columns={
            "index": _integer("VAP table index"),
            "essid": TextField(Title("ESSID")),
            "bssid": TextField(Title("BSSID")),
            "ap_mac": TextField(Title("AP MAC")),
            "channel": _integer("Channel"),
            "name": TextField(Title("Assigned Network Interface")),
            "radio": ChoiceField(Title("Frequency band"), mapping=_RADIO_BANDS),
            # Exact foreign-key-like reference to ``unifi_wifi_radios.name``.
            "radio_name": TextField(Title("Assigned Radio Identifier")),
            "bw": _integer("Bandwidth", "MHz"),
        },
    ),
)
