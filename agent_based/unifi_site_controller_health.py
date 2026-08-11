#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UnifiSites, as_int


def discover_unifi_site_controller_health(
        section: UnifiSites,
) -> DiscoveryResult:
    for health in section.root:
        subsystem = health.value("subsystem")
        if subsystem and health.value("status") != "unknown":
            yield Service(item=str(subsystem))


def check_unifi_site_controller_health(
        item: str,
        section: UnifiSites,
) -> CheckResult:
    health = next((entry for entry in section.root if entry.value("subsystem") == item), None)
    if health is None:
        return
    status = str(health.value("status", "unknown")).lower()
    yield Result(state=State.OK if status in {"ok", "healthy", "good"} else State.WARN, summary=f"Status: {status}")
    for name, label in (("num_adopted", "Adopted devices"), ("num_pending", "Pending devices"), ("num_disconnected", "Disconnected devices"), ("num_disabled", "Disabled devices")):
        if health.value(name) is not None:
            count = as_int(health.value(name))
            yield Result(state=State.WARN if name in {"num_pending", "num_disconnected"} and count else State.OK, summary=f"{label}: {count}")
    users, guests = as_int(health.value("num_user")), as_int(health.value("num_guest"))
    yield Metric("unifi_users", users)
    yield Metric("unifi_guests", guests)
    yield Result(state=State.OK, summary=f"Users: {users}, guests: {guests}")


check_plugin_unifi_site_controller_health = CheckPlugin(
    name="unifi_site_controller_health",
    service_name="UniFi Health %s",
    sections=["unifi_site_controller_health"],
    discovery_function=discover_unifi_site_controller_health,
    check_function=check_unifi_site_controller_health,
)
