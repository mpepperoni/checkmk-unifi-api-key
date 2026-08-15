#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.inventory_ui.v1_unstable import ChoiceField, Title
from cmk.plugins.collection.inventory_ui import networking


_DUPLEX_FIELD = ChoiceField(
    Title("Duplex"),
    mapping={
        "": "",
        "half": "half",
        "full": "full",
        "disagree": "disagree",
        "auto": "auto",
        "unknown": "unknown",
    },
)


def _add_duplex_column() -> None:
    """Extend Checkmk's interface table while preserving its existing columns."""
    columns = networking.node_networking_interfaces.table.columns
    if not isinstance(columns, dict):
        raise TypeError("The networking interface columns are not mutable")
    # A future Checkmk version or another add-on may already provide the
    # standard interface duplex column. Do not replace or add it a second time.
    if "duplex" in columns:
        return

    reordered_columns = {}
    for name, field in columns.items():
        reordered_columns[name] = field
        if name == "speed":
            reordered_columns["duplex"] = _DUPLEX_FIELD

    # Keep the column visible even if a future Checkmk version removes "speed".
    reordered_columns.setdefault("duplex", _DUPLEX_FIELD)
    columns.clear()
    columns.update(reordered_columns)


_add_duplex_column()
