#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.rulesets.v1 import Title
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    Float,
    InputHint,
    LevelDirection,
    LevelsType,
    SimpleLevels,
)
from cmk.rulesets.v1.form_specs.validators import NumberInRange
from cmk.rulesets.v1.rule_specs import CheckParameters, HostCondition, Topic


def _parameter_valuespec_unifi_device_poe() -> Dictionary:
    return Dictionary(
        title=Title("UniFi PoE budget levels"),
        elements={
            "poe_total_used_power_levels_upper": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Upper total PoE power usage"),
                    form_spec_template=Float(
                        unit_symbol="W",
                        custom_validate=(NumberInRange(0, 1000),),
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_levels_type=DefaultValue(LevelsType.NONE),
                    prefill_fixed_levels=InputHint((350, 400)),
                ),
            ),
            "poe_total_usage_levels_upper": DictElement(
                required=False,
                parameter_form=SimpleLevels(
                    title=Title("Upper total PoE budget usage"),
                    form_spec_template=Float(
                        unit_symbol="%",
                        custom_validate=(NumberInRange(0, 100),),
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_levels_type=DefaultValue(LevelsType.FIXED),
                    prefill_fixed_levels=DefaultValue((95, 98)),
                ),
            ),
        },
    )


rule_spec_unifi_device_poe = CheckParameters(
    name="unifi_device_poe",
    title=Title("UniFi PoE budget levels"),
    topic=Topic.POWER,
    parameter_form=_parameter_valuespec_unifi_device_poe,
    condition=HostCondition(),
)
