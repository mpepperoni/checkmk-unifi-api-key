#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UniFiDevice, UniFiUsers, as_int


def _item(
        vap,
) -> str:
    return f"{vap.value('name', 'unknown')}_{vap.value('essid', 'unknown')}"


def discover_unifi_device_wifi(
        section_unifi_device: UniFiDevice | None,
        section_unifi_device_users: UniFiUsers | None,
) -> DiscoveryResult:
    if section_unifi_device is None:
        return
    for vap in section_unifi_device.vap_table:
        yield Service(item=_item(vap))


def check_unifi_device_wifi(
        item: str,
        section_unifi_device: UniFiDevice | None,
        section_unifi_device_users: UniFiUsers | None,
) -> CheckResult:
    if section_unifi_device is None:
        return
    vap = next((entry for entry in section_unifi_device.vap_table if _item(entry) == item), None)
    if vap is None:
        return
    users = as_int(vap.value("num_sta"))
    signal = as_int(vap.value("avg_client_signal"))
    yield Result(state=State.OK if vap.value("up") else State.WARN, summary=f"SSID: {vap.value('essid', 'unknown')} ({'up' if vap.value('up') else 'down'})")
    yield Metric("unifi_clients", users)
    yield Metric("unifi_signal", signal)
    yield Result(state=State.OK, summary=f"Clients: {users}, average signal: {signal} dBm")
    if section_unifi_device_users:
        for user in section_unifi_device_users.root:
            if f"{user.value('radio_name')}_{user.value('essid')}" == item:
                yield Result(state=State.OK, notice=f"Client: {user.hostname or user.name or user.value('mac', 'unknown')} ({user.ip or 'no IP'})")


check_plugin_unifi_device_wifi = CheckPlugin(
    name="unifi_device_wifi",
    service_name="UniFi SSID %s",
    sections=["unifi_device", "unifi_device_users"],
    discovery_function=discover_unifi_device_wifi,
    check_function=check_unifi_device_wifi,
)
