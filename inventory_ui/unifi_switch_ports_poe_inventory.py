#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
"""Checkmk 2.5 inventory UI definition for UniFi PoE interfaces."""

from collections.abc import Iterable

from cmk.inventory_ui.v1_unstable import (
    BackgroundColor,
    ChoiceField,
    Node,
    Table,
    TextField,
    Title,
    View,
)
from cmk_addons.plugins.unifi.agent_based.unifi_switch_ports_poe_inventory import (
    poe_capabilities_mapping,
    poe_capable_mapping,
    poe_class_mapping,
    poe_enabled_mapping,
    poe_mode_mapping,
)


def _choice_mapping(values: dict[object, str]) -> dict[str, str]:
    """Use the generated inventory values as the selectable UI values."""
    return {value: value for value in values.values()}


def _style_poe_capable(value: str) -> Iterable[BackgroundColor]:
    if value == poe_capable_mapping[True]:
        yield BackgroundColor.LIGHT_GREEN
    else:
        yield BackgroundColor.DARK_GRAY


node_networking_unifi_interfaces_poe = Node(
    name="networking_unifi_interfaces_poe",
    path=["networking", "unifi_interfaces_poe"],
    title=Title("Unifi PoE Interfaces"),
    table=Table(
        view=View(name="invunifiinterfacespoe", title=Title("Unifi PoE Interfaces")),
        columns={
            "index": TextField(Title("Index")),
            "descr": TextField(Title("Description")),
            "alias": TextField(Title("Alias")),
            "poe_capable": ChoiceField(
                Title("PoE capable"),
                mapping=_choice_mapping(poe_capable_mapping),
                style=_style_poe_capable,
            ),
            "poe_capabilities": ChoiceField(
                Title("PoE capabilities"),
                mapping=_choice_mapping(poe_capabilities_mapping),
            ),
            "poe_enabled": ChoiceField(
                Title("PoE enabled"),
                mapping=_choice_mapping(poe_enabled_mapping),
            ),
            "poe_mode": ChoiceField(
                Title("PoE mode"),
                mapping=_choice_mapping(poe_mode_mapping),
            ),
            "poe_class": ChoiceField(
                Title("PoE class"),
                mapping=_choice_mapping(poe_class_mapping),
            ),
        },
    ),
)
