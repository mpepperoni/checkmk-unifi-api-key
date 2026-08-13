#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import BooleanChoice, DefaultValue, DictElement, Dictionary
from cmk.rulesets.v1.rule_specs import InventoryParameters, Topic


def _parameter_valuespec_unifi_inventory() -> Dictionary:
    return Dictionary(
        title=Title("UniFi inventory"),
        help_text=Help(
            "Select which UniFi inventory data should be inventoried."
        ),
        elements={
            "enable_interface": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    label=Label("Enable UniFi interface inventory"),
                    prefill=DefaultValue(True),
                ),
            ),
            "enable_lldp": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    label=Label("Enable UniFi LLDP inventory"),
                    prefill=DefaultValue(True),
                ),
            ),
        },
    )


rule_spec_unifi_inventory = InventoryParameters(
    name="unifi_inventory",
    title=Title("UniFi inventory"),
    topic=Topic.NETWORKING,
    parameter_form=_parameter_valuespec_unifi_inventory,
)
