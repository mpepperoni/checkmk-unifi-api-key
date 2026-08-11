#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import DEVICE_STATES, UnifiDevice, as_float, as_int, model_name


def discover_unifi_device(
        section: UnifiDevice,
) -> DiscoveryResult:
    yield Service(item="Device")
    if section.value("has_temperature") or section.value("has_fan"):
        yield Service(item="Environment")


def check_unifi_device(
        item: str,
        section: UnifiDevice,
) -> CheckResult:
    if item == "Device":
        state = as_int(section.state, -1)
        yield Result(state=State.OK if state == 1 else State.WARN if state == 2 else State.CRIT, summary=f"State: {DEVICE_STATES.get(state, 'unknown')}")
        yield Result(state=State.OK, summary=f"Type: {section.type or 'unknown'}, model: {model_name(section.model)}")
        yield Result(state=State.OK, summary=f"Name: {section.name or 'unknown'}, serial: {section.serial or 'unknown'}")
        yield Result(state=State.OK, summary=f"Version: {section.version or 'unknown'}, IP: {section.ip or 'unknown'}")
        satisfaction = as_int(section.value("satisfaction"))
        yield Metric("unifi_satisfaction", satisfaction, boundaries=(0, 100))
        yield Result(state=State.OK, summary=f"Satisfaction: {satisfaction}%")
        yield Result(state=State.OK if section.adopted else State.WARN, summary="Adopted" if section.adopted else "Waiting for adoption")
        for name, label in (("model_in_eol", "Model EOL"), ("model_in_lts", "Model LTS"), ("model_incompatible", "Model incompatible")):
            if section.value(name) is not None:
                yield Result(state=State.WARN if section.value(name) else State.OK, notice=f"{label}: {bool(section.value(name))}")
    elif item == "Environment":
        if section.value("has_temperature") and section.value("general_temperature") is not None:
            temperature = as_float(section.value("general_temperature"))
            yield Metric("unifi_temperature", temperature)
            yield Result(state=State.CRIT if section.value("overheating") else State.OK, summary=f"Temperature: {temperature:.1f} °C")
        if section.value("has_fan"):
            yield Result(state=State.OK, summary=f"Fan level: {as_int(section.value('fan_level'))}%")


check_plugin_unifi_device = CheckPlugin(
    name="unifi_device",
    service_name="UniFi %s",
    sections=["unifi_device"],
    discovery_function=discover_unifi_device,
    check_function=check_unifi_device,
)
