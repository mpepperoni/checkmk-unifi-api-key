#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import (
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    DefaultValue,
    DictElement,
    DictGroup,
    Dictionary,
    FieldSize,
    FixedValue,
    Integer,
    InputHint,
    List,
    Password,
    String,
    migrate_to_password,
    validators
)
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


def _form_spec_special_agent_unifi() -> Dictionary:
    api_config=DictGroup(title=Title("API configuration"))
    return Dictionary(
        title=Title("UniFi Controller"),
        help_text=Help("Query a UniFi Network controller via its HTTPS API."),
        elements={
            "hostname": DictElement(
                required=False,
                parameter_form=String(
                    title=Title("Use different Controller IP or DNS hostname."),
                    custom_validate=(validators.LengthInRange(min_value=1),)
                )
            ),
            "username": DictElement(
                required=False,
                parameter_form=String(
                    title=Title("Username"),
                    custom_validate=(validators.LengthInRange(min_value=1),)
                )
            ),
            "password": DictElement(
                required=False,
                parameter_form=Password(
                    title=Title("Password"),
                    migrate=migrate_to_password
                )
            ),
            "port": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("HTTPS port"),
                    prefill=DefaultValue(443),
                    custom_validate=(validators.NetworkPort(),)
                )
            ),
            "api_key": DictElement(
                required=False,
                parameter_form=Password(
                    title=Title("Local Network Integration API key"),
                    help_text=Help("Create a local key under Network Integrations and store it in the password store. Remove username/password, UDM-Pro and client piggyback options when using this backend. Device piggyback uses unifi- followed by the device MAC without separators. Sites match UUID, internal reference or exact display name."),
                    migrate=migrate_to_password,
                ),
            ),
            "no_cert_check": DictElement(
                required=False,
                parameter_form=FixedValue(
                    value=True,
                    title=Title("Certificate validation"),
                    label=Label("Disable certificate validation"),
                )
            ),
            "udm_pro": DictElement(
                required=False,
                group=api_config,
                parameter_form=FixedValue(
                    value=True,
                    help_text=Help("Use UDM-Pro API endpoints instead the old UniFi API."),
                    title=Title("UDM-Pro API"),
                    label=Label("Use UDM-Pro API endpoints"),
                )
            ),
            "sites": DictElement(
                required=False,
                group=api_config,
                parameter_form=List(
                    title=Title("Sites"),
                    help_text=Help('Disabled will query all sites. Use "all" explicitly to make this setting visible.'),
                    element_template=String(
                        title=Title("Site"),
                        prefill=DefaultValue("all")),
                ),
            ),
            "device_piggyback": DictElement(
                required=False,
                group=api_config,
                parameter_form=FixedValue(
                    value=True,
                    title=Title("Device piggyback"),
                    label=Label("Create piggyback data for UniFi devices"),
                ),
            ),
            "user_piggyback": DictElement(
                required=False,
                group=api_config,
                parameter_form=Dictionary(
                    title=Title("User piggyback. Will create Services on all Devices where the selected Piggyback filed will match."),
                    elements={
                        "user_piggyback_name": DictElement(
                            required=True,
                            parameter_form=CascadingSingleChoice(
                                title=Title("User piggyback host name field"),
                                elements=[
                                    CascadingSingleChoiceElement(
                                        name="ip",
                                        title=Title("IP"),
                                        parameter_form=FixedValue(value=None),
                                    ),
                                    CascadingSingleChoiceElement(
                                        name="hostname",
                                        title=Title("Hostname"),
                                        parameter_form=FixedValue(value=None),
                                    ),
                                    CascadingSingleChoiceElement(
                                        name="hostname_domain",
                                        title=Title("Hostname with Domain"),
                                        parameter_form=Dictionary(
                                            elements={
                                                "domain": DictElement(
                                                    required=True,
                                                    parameter_form=String(
                                                        title=Title("Domain"),
                                                        prefill=InputHint("mydomain.com"),
                                                        field_size=FieldSize.MEDIUM,
                                                        custom_validate=(
                                                            validators.MatchRegex(
                                                                r"^(?=.{1,253}$)(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+(?!-)[A-Za-z0-9-]{2,63}(?<!-)$"
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            },
                                        ),
                                    ),
                                ],
                                prefill=DefaultValue("ip"),
                            ),
                        ),
                    },
                ),
            ),
            "user_piggyback_site": DictElement(
                required=False,
                group=api_config,
                parameter_form=FixedValue(
                    value=True,
                    title=Title("User piggyback on site host"),
                    label=Label("Create user services on the UniFi site host"),
                ),
            ),
        },
    )


rule_spec_unifi = SpecialAgent(
    name="unifi",
    title=Title("UniFi connection parameters"),
    topic=Topic.NETWORKING,
    parameter_form=_form_spec_special_agent_unifi,
)
