"""Parameter form for the UniFi special agent."""
from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import BooleanChoice, DictElement, Dictionary, Integer, List, Password, String, migrate_to_password, validators
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


def _form_spec_special_agent_unifi() -> Dictionary:
    return Dictionary(
        title=Title("UniFi Controller"), help_text=Help("Query a UniFi Network controller via its HTTPS API."),
        elements={
            "hostname": DictElement(required=True, parameter_form=String(title=Title("Controller hostname"), custom_validate=(validators.LengthInRange(min_value=1),))),
            "username": DictElement(required=True, parameter_form=String(title=Title("Username"), custom_validate=(validators.LengthInRange(min_value=1),))),
            "password": DictElement(required=True, parameter_form=Password(title=Title("Password"), migrate=migrate_to_password)),
            "port": DictElement(required=False, parameter_form=Integer(title=Title("HTTPS port"), prefill=443, custom_validate=(validators.NetworkPort(),))),
            "udm_pro": DictElement(required=False, parameter_form=BooleanChoice(title=Title("UDM-Pro API"), label=Label("Use UDM-Pro API endpoints"))),
            "sites": DictElement(
                required=False,
                parameter_form=List(
                    title=Title("Sites"),
                    help_text=Help('Leave empty to query all sites. Use "all" explicitly to make this setting visible.'),
                    element_template=String(title=Title("Site")),
                ),
            ),
            "device_piggyback": DictElement(required=False, parameter_form=BooleanChoice(title=Title("Device piggyback"), label=Label("Create piggyback data for UniFi devices"))),
            "user_piggyback": DictElement(required=False, parameter_form=String(title=Title("User piggyback mode"), help_text=Help("Use create_user or create_user_site."))),
            "user_piggyback_name": DictElement(required=False, parameter_form=String(title=Title("User piggyback host name field"), prefill="ip")),
            "no_cert_check": DictElement(required=False, parameter_form=BooleanChoice(title=Title("Certificate validation"), label=Label("Disable certificate validation"))),
        },
    )


rule_spec_unifi = SpecialAgent(name="unifi", title=Title("UniFi connection parameters"), topic=Topic.NETWORKING, parameter_form=_form_spec_special_agent_unifi)
