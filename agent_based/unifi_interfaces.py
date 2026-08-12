#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from collections import defaultdict
from collections.abc import Mapping, Sequence
from time import time
from typing import Any

from cmk.agent_based.v2 import (
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    RuleSetType,
    Service,
    ServiceLabel,
    State,
    check_levels,
)
from cmk.plugins.lib import interfaces

from .unifi import UniFiInterfaces, UnifiInterface


def _interfaces_section(section: UniFiInterfaces) -> list[interfaces.InterfaceWithCounters]:
    """Expose UniFi port fields with the same attributes as Checkmk's SNMP interface check."""
    timestamp = time()
    interface_section = []
    for port in section.root.values():
        rx_broadcast = port.rx_broadcast or 0
        rx_multicast = port.rx_multicast or 0
        tx_broadcast = port.tx_broadcast or 0
        tx_multicast = port.tx_multicast or 0
        interface_section.append(
            interfaces.InterfaceWithCounters(
                attributes=interfaces.Attributes(
                    index=str(port.port_idx),
                    descr=f"Port {port.port_idx}",
                    alias=port.name,
                    type="6",  # ethernetCsmacd
                    speed=(port.speed or 0) * 1_000_000,
                    oper_status="1" if port.up else "2",
                    admin_status=(
                        None
                        if (enabled := port.enabled if port.enabled is not None else port.enable) is None
                        else "1" if enabled else "2"
                    ),
                ),
                counters=interfaces.Counters(
                    in_octets=port.rx_bytes,
                    in_ucast=max(0, (port.rx_packets or 0) - rx_broadcast - rx_multicast),
                    in_mcast=rx_multicast,
                    in_bcast=rx_broadcast,
                    in_disc=port.rx_dropped,
                    in_err=port.rx_errors,
                    out_octets=port.tx_bytes,
                    out_ucast=max(0, (port.tx_packets or 0) - tx_broadcast - tx_multicast),
                    out_mcast=tx_multicast,
                    out_bcast=tx_broadcast,
                    out_disc=port.tx_dropped,
                    out_err=port.tx_errors,
                ),
                timestamp=timestamp,
            )
        )
    return interface_section


def _port(
        item: str,
        params: Mapping[str, Any],
        section: UniFiInterfaces,
) -> UnifiInterface | None:
    appearance = params.get("item_appearance")
    for interface in interfaces.matching_interfaces_for_item(
            item,
            _interfaces_section(section),
            interfaces._to_item_appearance(appearance) if appearance else None,
    ):
        return section.root.get(interface.attributes.index)
    return None


def discover_unifi_device_if(
        params: Sequence[Mapping[str, Any]],
        section: UniFiInterfaces,
) -> DiscoveryResult:
    interface_section = _interfaces_section(section)
    if not interface_section:
        return

    pre_inventory: list[tuple[str, dict[str, object], int, bool, dict[str, str]]] = []
    seen_indices: set[str] = set()
    item_occurrences: dict[str, int] = defaultdict(int)

    for interface in interface_section:
        # Match Checkmk's standard interface discovery: an interface is only
        # discovered after a discovery rule has matched it.  In particular, the
        # default rule limits discovery to operationally up ports.
        discover = False
        settings = interfaces.DISCOVERY_DEFAULT_PARAMETERS["discovery_single"][1]
        for rule in params:
            if "discovery_single" in rule and interfaces._check_single_matching_conditions(
                    interface.attributes, rule["matching_conditions"][1]
            ):
                discover, settings = rule["discovery_single"]
                break

        pad_portnumbers = settings.get("pad_portnumbers", True)
        for appearance in ("index", "descr", "alias"):
            if appearance == "alias" and interface.attributes.alias == interface.attributes.descr:
                continue
            item_occurrences[interfaces._compute_item(
                interfaces._to_item_appearance(appearance),
                interface.attributes,
                interface_section,
                pad_portnumbers,
            ).item] += 1

        item_info = interfaces._compute_item(
            interfaces._to_item_appearance(settings.get("item_appearance", "index")),
            interface.attributes,
            interface_section,
            pad_portnumbers,
        )
        if not discover or interface.attributes.index in seen_indices:
            continue

        labels: dict[str, str] = {}
        for label_condition in settings.get("labels_conditions", []):
            conditions = label_condition.get("conditions", {})
            if (
                interfaces.check_regex_match_conditions(interface.attributes.index, conditions.get("match_index"))
                and interfaces.check_regex_match_conditions(interface.attributes.alias, conditions.get("match_alias"))
                and interfaces.check_regex_match_conditions(interface.attributes.descr, conditions.get("match_desc"))
            ):
                labels.update(label_condition.get("labels", {}))
        labels.update(settings.get("labels", {}))

        port = section.root.get(interface.attributes.index)
        if port is not None:
            if port.port_poe and port.poe_enable:
                labels["cmk/has_poe_active"] = "true"
            if port.is_uplink:
                labels["cmk/is_upline_true"] = "true"

        discovered_params: dict[str, object] = {
            "item_appearance": item_info.used_appearance,
            "discovered_oper_status": [interface.attributes.oper_status],
            "discovered_speed": interface.attributes.speed,
        }
        if interface.attributes.admin_status is not None:
            discovered_params["discovered_admin_status"] = [interface.attributes.admin_status]

        pre_inventory.append((
            item_info.item,
            discovered_params,
            int(interface.attributes.index),
            item_info.used_appearance == "index",
            labels,
        ))
        seen_indices.add(interface.attributes.index)

    for item, discovered_params, index, index_as_item, labels in pre_inventory:
        yield Service(
            item=f"{item} {index}" if not index_as_item and item_occurrences[item] > 1 else item,
            parameters=discovered_params,
            labels=[ServiceLabel(key, value) for key, value in labels.items()] or None,
        )


def check_unifi_device_if(
        item: str,
        params: Mapping[str, Any],
        section: UniFiInterfaces,
) -> CheckResult:
    # Use the normal Checkmk interface implementation first. This makes the complete
    # ``interfaces`` check ruleset available, including status, speed, traffic,
    # packet/error levels, averaging and all standard interface metrics.
    yield from interfaces.check_multiple_interfaces(
        item,
        params,
        _interfaces_section(section),
    )

    port = _port(item, params, section)
    if port is None:
        return
    up = bool(port.up)

    satisfaction = port.satisfaction or 0
    yield Result(state=State.OK, notice=f"Jumbo frames: {'enabled' if port.jumbo else 'disabled'}")
    if up:
        yield from check_levels(
            satisfaction,
            metric_name="unifi_satisfaction",
            label="Satisfaction",
            render_func=lambda value: f"{value:.0f}%",
            boundaries=(0, 100),
        )
    if port.port_poe and port.poe_enable:
        yield Result(state=State.OK, notice="PoE:  enabled")
        yield Result(state=State.OK, notice=f"PoE mode: {port.poe_mode or 'unknown'}")
        yield Result(state=State.OK if port.poe_good is not False else State.WARN, notice=f"PoE status: {port.poe_good or 'unknown'}")
        if port.poe_class:
            yield Result(state=State.OK, notice=f"PoE class: {port.poe_class}")

        # voltage
        if port.poe_voltage is not None:
            yield from check_levels(
                port.poe_voltage,
                metric_name="unifi_poe_voltage",
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
    else:
        yield Result(state=State.OK, notice="PoE: disabled or no POE-Port")



check_plugin_unifi_interfaces = CheckPlugin(
    name="unifi_interfaces",
    service_name="Unifi Interface %s",
    sections=["unifi_device_if"],
    discovery_function=discover_unifi_device_if,
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    check_ruleset_name="interfaces",
    check_default_parameters=interfaces.CHECK_DEFAULT_PARAMETERS,
    check_function=check_unifi_device_if,
)
