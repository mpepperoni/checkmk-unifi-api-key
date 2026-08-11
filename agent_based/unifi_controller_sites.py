#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UniFiSite, UniFiSites, as_int


def discover_unifi_controller_sites(
        section: UniFiSites,
) -> DiscoveryResult:
    for site in section.root:
        if site.desc:
            yield Service(item=site.desc)


def check_unifi_controller_sites(
        item: str,
        section: UniFiSites,
) -> CheckResult:
    site = next((entry for entry in section.root if entry.desc == item), None)
    if site is None:
        return
    alarms = as_int(site.num_new_alarms)
    yield Result(state=State.WARN if alarms else State.OK, summary=f"Alarms: {alarms}")
    yield Result(state=State.OK, summary=f"Site ID: {site.name or 'unknown'}")
    for health in site.health:
        users = as_int(health.value("num_user"))
        guests = as_int(health.value("num_guest"))
        yield Result(state=State.OK, notice=f"{health.value('subsystem', 'unknown')}: {health.value('status', 'unknown')}, users: {users}, guests: {guests}")
        yield Metric("unifi_users", users)
        yield Metric("unifi_guests", guests)


check_plugin_unifi_controller_sites = CheckPlugin(
    name="unifi_controller_sites",
    service_name="UniFi Site %s",
    sections=["unifi_controller_sites"],
    discovery_function=discover_unifi_controller_sites,
    check_function=check_unifi_controller_sites,
)
