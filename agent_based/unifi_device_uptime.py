#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Metric,
    Result,
    Service,
    State,
    render
)
from .unifi import UnifiDevice


def discover_unifi_device_uptime(
        section: UnifiDevice,
) -> DiscoveryResult:
    if section.uptime is not None:
        yield Service()


def check_unifi_device_uptime(
        section: UnifiDevice,
) -> CheckResult:
    if section.uptime is None:
        return
    yield Result(state=State.OK, summary=f"Uptime: {render.timespan(section.uptime)}")
    yield Metric("uptime", section.uptime)


check_plugin_unifi_device_uptime = CheckPlugin(
    name="unifi_device_uptime",
    service_name="UniFi Uptime",
    sections=["unifi_device"],
    discovery_function=discover_unifi_device_uptime,
    check_function=check_unifi_device_uptime,
)
