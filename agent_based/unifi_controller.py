from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Result, Service, State
from .unifi import UniFiController


def discover_unifi_controller(section: UniFiController) -> DiscoveryResult:
    yield Service()


def check_unifi_controller(section: UniFiController) -> CheckResult:
    yield Result(state=State.OK, summary=f"Name: {section.name or 'unknown'}")
    yield Result(state=State.OK, summary=f"Type: {section.ubnt_device_type or section.type or 'unknown'}")
    yield Result(state=State.OK, summary=f"Build: {section.build or 'unknown'}")
    unsupported = section.unsupported_device_count or 0
    yield Result(
        state=State.WARN if unsupported else State.OK,
        summary=f"Unsupported devices: {unsupported}",
    )
    if section.unsupported_device_list:
        yield Result(state=State.OK, notice=f"Unsupported device models: {', '.join(section.unsupported_device_list)}")


check_plugin_unifi_controller = CheckPlugin(
    name="unifi_controller", service_name="UniFi Controller", sections=["unifi_controller"],
    discovery_function=discover_unifi_controller, check_function=check_unifi_controller,
)
