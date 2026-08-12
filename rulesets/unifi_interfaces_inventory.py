#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import BooleanChoice, DefaultValue, DictElement, Dictionary
from cmk.rulesets.v1.rule_specs import InventoryParameters, Topic


def _parameter_valuespec_unifi_interfaces_inventory() -> Dictionary:
    return Dictionary(
        title=Title("UniFi interface inventory"),
        help_text=Help(
            "Disable this inventory when the same interfaces are already inventoried "
            "through an other inventory funktion like SNMP."
        ),
        elements={
            "enabled": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    label=Label("Enable UniFi interface inventory"),
                    prefill=DefaultValue(True),
                ),
            ),
        },
    )


rule_spec_unifi_interfaces_inventory = InventoryParameters(
    name="unifi_interfaces_inventory",
    title=Title("UniFi interface inventory"),
    topic=Topic.NETWORKING,
    parameter_form=_parameter_valuespec_unifi_interfaces_inventory,
)
