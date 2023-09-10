#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
#  _   _       _  __ _ 
# | | | |     (_)/ _(_)
# | | | |_ __  _| |_ _ 
# | | | | '_ \| |  _| |
# | |_| | | | | | | | |
#  \___/|_| |_|_|_| |_|
#
# created: 01/2022
#
# Author: Frank Baier
# E-Mail: dev@baier-nt.de
#
from cmk.gui.plugins.wato.special_agents.common import RulespecGroupDatasourceProgramsHardware
from cmk.gui.i18n import _
from cmk.gui.plugins.wato.utils import (
    HostRulespec,
    IndividualOrStoredPassword,
    rulespec_registry,
)
from cmk.gui.valuespec import (
    Checkbox,
    Dictionary,
    DropdownChoice,
    Integer,
    ListOfStrings,
    TextAscii,
    Transform,
)


def _special_agents_unifi_transform(v):
    v.setdefault("verify_cert", False)
    v.setdefault("port", 8443)
    v.setdefault("sites", ["all"])
    return v


def _valuespec_special_agents_unifi():
    return Transform(
        Dictionary(
            title=_("Unifi Controller1"),
            elements=[
                ("user", TextAscii(
                    title=_("Username"),
                    allow_empty=False,
                )),
                ("password", IndividualOrStoredPassword(
                    title=_("Password"),
                    allow_empty=False,
                )),
                ("port",
                 Integer(
                     title=_('TCP port number'),
                     help=_('Port number that the Unifi Controller is listening on. The default is 8443.'
                            'The new Controller generation (G2) uses 443.'),
                     default_value=8443,
                     minvalue=1,
                     maxvalue=65535,
                 )),
                ("verify_cert",
                 DropdownChoice(
                     title=_("SSL certificate verification"),
                     default_value=False,
                     choices=[
                         (True, _("Activate")),
                         (False, _("Deactivate")),
                     ],
                 )),
                ("controller", TextAscii(
                    title=_("Controller"),
                    help=_('Unifi controller IP or hostname (extra value in case a docker overlay network is used)'),
                    allow_empty=True,
                )),
                ("use_hostname",
                 Checkbox(
                     title=_("Use hostname"),
                     label=_("Use hostname instead of IP for check execution. If a special hostname is set "
                             "this will be overwritten."),
                     default_value=False,
                     true_label=_("use hostname"),
                     false_label=_("use IP"),
                 )),
                ("sites",
                 ListOfStrings(
                     title=_("Sites to query"),
                     help=_("Use this option to set which sites should be checked by the special agent."
                            "If this is disabled only overall information is given."
                            "If you enabled it and set \"all\", all sites are given"),
                     size=32,
                     allow_empty=True,
                 )),
            ],
            optional_keys=["sites", 'controller'],
        ),
        forth=_special_agents_unifi_transform,
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupDatasourceProgramsHardware,
        name="special_agents:unifi",
        title=lambda: _("Unifi Controller"),
        valuespec=_valuespec_special_agents_unifi,
    ))
