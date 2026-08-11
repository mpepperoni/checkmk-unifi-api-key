#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from collections.abc import Mapping
from typing import Any
from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    check_levels,
)
from .unifi import UnifiDevice


DEFAULT_PARAMETERS = {
    "poe_total_usage_levels_upper": ("fixed", (95.0, 98.0)),
    "unifi_poe_total_used_power": ("no_levels", None),
}


def discover_unifi_device_poe(
        section: UnifiDevice
) -> DiscoveryResult:
    if section.total_used_power:
        yield Service()


def check_unifi_device_poe(
    params: Mapping[str, Any],
    section: UnifiDevice,
) -> CheckResult:

    if (used_power := section.total_used_power) is not None:
        yield from check_levels(
            used_power,
            levels_upper=params.get("poe_total_used_power_levels_upper"),
            metric_name="unifi_poe_total_used_power",
            label="PoE power used",
            render_func=lambda value: f"{value:.2f} W",
        )

    max_power = section.total_max_power
    max_effective_power = section.total_max_effective_power

    if max_power is not None:
        yield Result(state=State.OK, summary=f"Maximum PoE power: {max_power} W")

    if max_effective_power is not None:
        yield Result(state=State.OK, summary=f"Maximum effective PoE power: {max_effective_power} W")

    maxpower = max_power or max_effective_power

    if maxpower is not None and maxpower > 0 and used_power is not None:
        percentage = used_power / maxpower * 100
        yield from check_levels(
            percentage,
            levels_upper=params.get("poe_total_usage_levels_upper"),
            metric_name="unifi_poe_total_usage",
            label="PoE budget usage",
            render_func=lambda value: f"{value:.1f}%",
            boundaries=(0, 100),
        )


check_plugin_unifi_device_poe = CheckPlugin(
    name="unifi_device_poe",
    service_name="Unifi PoE budget",
    sections=["unifi_device"],
    discovery_function=discover_unifi_device_poe,
    check_function=check_unifi_device_poe,
    check_ruleset_name="unifi_device_poe",
    check_default_parameters=DEFAULT_PARAMETERS,
)
