#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UniFiUser, UniFiUsers, as_int


def _item(
        user: UniFiUser,
) -> str:
    return str(user.hostname or user.name or user.value("mac") or user.value("_id", "unknown"))


def discover_unifi_site_users(
        section: UniFiUsers,
) -> DiscoveryResult:
    for user in section.root:
        yield Service(item=_item(user))


def check_unifi_site_users(
        item: str,
        section: UniFiUsers
) -> CheckResult:
    user = next((entry for entry in section.root if _item(entry) == item), None)
    if user is None:
        return
    satisfaction = as_int(user.value("satisfaction"))
    state = State.OK if user.value("is_online", True) else State.WARN
    yield Result(state=state, summary=f"IP: {user.ip or 'unknown'}, network: {user.value('network', 'unknown')}")
    yield Metric("unifi_satisfaction", satisfaction, boundaries=(0, 100))
    yield Result(state=State.OK, summary=f"Satisfaction: {satisfaction}%")


check_plugin_unifi_site_users = CheckPlugin(
    name="unifi_site_users",
    service_name="UniFi Client %s",
    sections=["unifi_site_users"],
    discovery_function=discover_unifi_site_users,
    check_function=check_unifi_site_users,
)
