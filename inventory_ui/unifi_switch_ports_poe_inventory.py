#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
"""Checkmk 2.5 inventory UI definition for UniFi PoE interfaces."""

from cmk.inventory_ui.v1_unstable import ChoiceField, Node, Table, TextField, Title, View


node_networking_interfaces_poe = Node(
    name="networking_interfaces_poe",
    path=["networking", "interfaces_poe"],
    title=Title("PoE interfaces"),
    table=Table(
        view=View(name="invunifiinterfacespoe", title=Title("PoE interfaces")),
        columns={
            "index": TextField(Title("Index")),
            "descr": TextField(Title("Description")),
            "alias": TextField(Title("Alias")),
            "poe_capable": ChoiceField(
                Title("PoE capable"),
                mapping={
                    "Capable": "Capable",
                    "Not capable": "Not capable",
                },
            ),
            "poe_capabilities": ChoiceField(
                Title("PoE capabilities"),
                mapping={
                    "Not supported": "Not supported",
                    "Supported (capability mask: 1)": "Supported (capability mask: 1)",
                    "Supported (capability mask: 3)": "Supported (capability mask: 3)",
                    "Supported (capability mask: 7)": "Supported (capability mask: 7)",
                },
            ),
            "poe_enabled": ChoiceField(
                Title("PoE enabled"),
                mapping={
                    "Enabled": "Enabled",
                    "Disabled": "Disabled",
                },
            ),
            "poe_mode": ChoiceField(
                Title("PoE mode"),
                mapping={
                    "auto": "Automatic",
                    "off": "Off",
                    "pasv24": "Passive 24 V",
                },
            ),
            "poe_class": ChoiceField(
                Title("PoE class"),
                mapping={
                    "Unknown": "Unknown",
                    "Class 0": "Class 0",
                    "Class 1": "Class 1",
                    "Class 2": "Class 2",
                    "Class 3": "Class 3",
                    "Class 4": "Class 4",
                },
            ),
        },
    ),
)
