#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#from cmk.graphing.v1 import Title
from cmk.graphing.v1.graphs import Graph, MinimalRange, Title
from cmk.graphing.v1.metrics import Color, DecimalNotation, Metric, Unit


metric_unifi_users = Metric(
    name="unifi_users",
    title=Title("UniFi users"),
    unit=Unit(DecimalNotation("")),
    color=Color.LIGHT_BLUE,
)
metric_unifi_guests = Metric(
    name="unifi_guests",
    title=Title("UniFi guests"),
    unit=Unit(DecimalNotation("")),
    color=Color.LIGHT_GREEN,
)
metric_unifi_clients = Metric(
    name="unifi_clients",
    title=Title("Connected clients"),
    unit=Unit(DecimalNotation("")),
    color=Color.LIGHT_BLUE,
)
metric_unifi_satisfaction = Metric(
    name="unifi_satisfaction",
    title=Title("WiFi satisfaction"),
    unit=Unit(DecimalNotation("%")),
    color=Color.LIGHT_GREEN,
)
metric_unifi_signal = Metric(
    name="unifi_signal",
    title=Title("Signal strength"),
    unit=Unit(DecimalNotation("dBm")),
    color=Color.LIGHT_BLUE,
)
metric_unifi_noise = Metric(
    name="unifi_noise",
    title=Title("Noise level"),
    unit=Unit(DecimalNotation("dBm")),
    color=Color.LIGHT_RED,
)
metric_unifi_temperature = Metric(
    name="unifi_temperature",
    title=Title("Temperature"),
    unit=Unit(DecimalNotation("°C")),
    color=Color.LIGHT_RED,
)
metric_unifi_poe_power = Metric(
    name="unifi_poe_power",
    title=Title("PoE power"),
    unit=Unit(DecimalNotation("W")),
    color=Color.LIGHT_GREEN,
)
metric_unifi_channel = Metric(
    name="unifi_channel",
    title=Title("WiFi channel"),
    unit=Unit(DecimalNotation("")),
    color=Color.LIGHT_BLUE,
)
metric_unifi_if_rx_bytes = Metric(
    name="unifi_if_rx_bytes",
    title=Title("Received bytes"),
    unit=Unit(DecimalNotation("B")),
    color=Color.LIGHT_BLUE,
)
metric_unifi_if_tx_bytes = Metric(
    name="unifi_if_tx_bytes",
    title=Title("Sent bytes"),
    unit=Unit(DecimalNotation("B")),
    color=Color.LIGHT_GREEN,
)
metric_unifi_if_rx_errors = Metric(
    name="unifi_if_rx_errors",
    title=Title("Receive errors"),
    unit=Unit(DecimalNotation("")),
    color=Color.LIGHT_RED,
)
metric_unifi_if_tx_errors = Metric(
    name="unifi_if_tx_errors",
    title=Title("Transmit errors"),
    unit=Unit(DecimalNotation("")),
    color=Color.LIGHT_RED,
)

graph_unifi_users = Graph(
    name="unifi_users",
    title=Title("UniFi clients"),
    simple_lines=["unifi_users", "unifi_guests"],
    minimal_range=MinimalRange(0, 1),
)
graph_unifi_interface_traffic = Graph(
    name="unifi_interface_traffic",
    title=Title("UniFi interface traffic"),
    simple_lines=["unifi_if_rx_bytes", "unifi_if_tx_bytes"],
    minimal_range=MinimalRange(0, 1),
)
