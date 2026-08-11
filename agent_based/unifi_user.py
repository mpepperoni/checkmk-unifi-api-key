#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UnifiUser, as_int


def discover_unifi_user(
        section: UnifiUser,
) -> DiscoveryResult:
    yield Service(item="Info")
    yield Service(item="Uplink")


def check_unifi_user(
        item: str,
        section: UnifiUser,
) -> CheckResult:
    if item == "Info":
        satisfaction = as_int(section.value("satisfaction"))
        yield Result(
            state=State.OK,
            summary=f"Hostname: {section.hostname or 'unknown'}, name: {section.name or 'unknown'}"
        )
        yield Result(
            state=State.OK,
            summary=f"IP: {section.ip or 'unknown'}, network: {section.value('network', 'unknown')}"
        )
        yield Metric("unifi_satisfaction", satisfaction, boundaries=(0, 100))
        yield Result(state=State.OK, summary=f"Satisfaction: {satisfaction}%")
    elif item == "Uplink":
        if section.value("is_wired"):
            yield Result(
                state=State.OK,
                summary=f"Switch: {section.value('uplink_name', 'unknown')}, port: {section.value('sw_port', 'unknown')}")
        else:
            signal, noise = as_int(section.value("signal")), as_int(section.value("noise"))
            yield Result(
                state=State.OK,
                summary=f"Access point: {section.value('uplink_name', 'unknown')}, radio: {section.value('radio_name', 'unknown')}"
            )
            yield Metric("unifi_signal", signal)
            yield Metric("unifi_noise", noise)
            yield Result(state=State.OK, summary=f"Signal: {signal} dBm, noise: {noise} dBm")


check_plugin_unifi_user = CheckPlugin(
    name="unifi_user",
    service_name="UniFi Client %s",
    sections=["unifi_user"],
    discovery_function=discover_unifi_user,
    check_function=check_unifi_user,
)
