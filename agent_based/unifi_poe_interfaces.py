#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from typing import Literal, TypeAlias
from collections.abc import Mapping, Sequence
from typing import Any
from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    RuleSetType,
    State,
    check_levels,
)
from cmk.plugins.lib import interfaces
from .unifi import UniFiInterfaces
from .unifi_interfaces import discover_unifi_device_if, port_for_item


NoLevelsT: TypeAlias = tuple[Literal["no_levels"], None]
FixedLevelsT: TypeAlias = tuple[Literal["fixed"], tuple[float, float]]
LevelsT: TypeAlias = NoLevelsT | FixedLevelsT
PoeVoltageLevelsT: TypeAlias = dict[
    str,
    dict[Literal["levels_lower", "levels_upper"], FixedLevelsT],
]


def poe_voltage_levels(
        poe_class: str | None,
        level: Literal['levels_lower', 'levels_upper']
) -> LevelsT:
    if poe_class is None:
        return ("no_levels", None)
    poe_class_voltage_levels: PoeVoltageLevelsT = {
        # Class 0-3: Type 1 (44-57 V)
        "Class 0": {
            "levels_lower": ("fixed", (44.2, 44.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
        "Class 1": {
            "levels_lower": ("fixed", (44.2, 44.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
        "Class 2": {
            "levels_lower": ("fixed", (44.2, 44.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
        "Class 3": {
            "levels_lower": ("fixed", (44.2, 44.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },

        # Class 4-6: Type 2/3 (50-57 V)
        "Class 4": {
            "levels_lower": ("fixed", (50.2, 50.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
        "Class 5": {
            "levels_lower": ("fixed", (50.2, 50.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
        "Class 6": {
            "levels_lower": ("fixed", (50.2, 50.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },

        # Class 7-8: Type 4 (52-57 V)
        "Class 7": {
            "levels_lower": ("fixed", (52.2, 52.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
        "Class 8": {
            "levels_lower": ("fixed", (52.2, 52.0)),
            "levels_upper": ("fixed", (56.8, 57.0)),
        },
    }
    class_levels = poe_class_voltage_levels.get(poe_class)
    levels = class_levels.get(level) if class_levels is not None else None
    return levels if levels is not None else ("no_levels", None)


def discover_unifi_poe_interfaces(
        params: Sequence[Mapping[str, Any]],
        section: UniFiInterfaces,
) -> DiscoveryResult:
    for service in discover_unifi_device_if(params, section):
        port = port_for_item(service.item, service.parameters, section)
        if port is not None and port.port_poe:
            yield service


def check_unifi_poe_interfaces(
        item: str,
        params: Mapping[str, Any],
        section: UniFiInterfaces,
) -> CheckResult:
    port = port_for_item(item, params, section)
    if port is None or not port.port_poe:
        return

    """
    | Feld          | Bedeutung                                                                 |
    | ------------- | ------------------------------------------------------------------------- |
    | `port_poe`    | Dieser physische Switchport **unterstützt PoE**                           |
    | `poe_caps`    | Bitmaske/Fähigkeiten des Ports bzgl. PoE                                  |
    | `poe_mode`    | Konfiguration des Ports, z. B. `auto`, `off`, ältere Geräte auch `pasv24` |
    | `poe_enable`  | PoE-Ausgabe ist auf diesem Port **aktiviert/freigegeben**                 |
    | `poe_good`    | Switch hat einen gültigen PoE-Zustand / ein PD erkannt und versorgt es    |
    | `poe_class`   | erkannte IEEE-PoE-Leistungsklasse des angeschlossenen PD                  |
    | `poe_voltage` | aktuell ausgegebene PoE-Spannung                                          |
    | `poe_current` | aktueller Strom                                                           |
    | `poe_power`   | aktuell abgegebene Leistung in Watt                                       |

    port_poe      → kann dieser Port PoE?
    poe_mode      → ist PoE administrativ erlaubt?
    poe_enable    → ist der PoE-Ausgang aktuell eingeschaltet?
    poe_good      → wurde ein gültiges PD erkannt / wird tatsächlich versorgt?
    """
    if port.poe_mode == "off":
        yield Result(state=State.OK, summary="PoE mode: disabled")
        return
    elif port.poe_mode == "pasv24":
        yield Result(state=State.OK, summary="PoE mode: 24V")
    elif port.poe_mode == "auto":
        yield Result(state=State.OK, summary="PoE mode: auto")
    else:
        yield Result(state=State.OK, summary="PoE mode: unknown")

    if not port.poe_enable:
        yield Result(state=State.OK, summary="PoE out: inactive")
        return
    else:
        yield Result(state=State.OK, summary="PoE out: active")

    if not port.up:
        return

    if not port.poe_good and port.poe_enable and port.poe_mode == "pasv24":
        yield Result(state=State.OK, summary="PoE state: permanent 24V")
    elif not port.poe_good and port.poe_enable:
        yield Result(state=State.WARN, summary="PoE state: bad")
        return
    else:
        yield Result(state=State.OK, summary="PoE state: good")

    # yield Result(state=State.OK, notice=f"PoE state: {port.poe_good or 'unknown'}")
    # yield Result(state=State.OK, notice=f"PoE mode: {port.poe_mode or 'unknown'}")
    if port.poe_class:
        yield Result(state=State.OK, summary=f"PoE class: {port.poe_class}")

    # voltage
    if port.poe_voltage is not None:
        yield from check_levels(
            port.poe_voltage,
            metric_name="unifi_poe_voltage",
            levels_lower=poe_voltage_levels(port.poe_class, "levels_lower"),
            levels_upper=poe_voltage_levels(port.poe_class, "levels_upper"),
            label="PoE voltage",
            render_func=lambda value: f"{value:.2f} V",
            notice_only=True,
        )

    # current
    if port.poe_current is not None:
        yield from check_levels(
            port.poe_current,
            metric_name="unifi_poe_current",
            label="PoE current",
            render_func=lambda value: f"{value:.2f} mA",
            notice_only=True,
        )

    # power
    poe_power = port.poe_power or 0.0
    yield from check_levels(
        poe_power,
        metric_name="unifi_poe_power",
        label="PoE power",
        render_func=lambda value: f"{value:.2f} W",
    )


check_plugin_unifi_poe_interfaces = CheckPlugin(
    name="unifi_poe_interfaces",
    service_name="Unifi PoE Interface %s",
    sections=["unifi_device_if"],
    discovery_function=discover_unifi_poe_interfaces,
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    check_function=check_unifi_poe_interfaces,
    check_default_parameters={},
)
