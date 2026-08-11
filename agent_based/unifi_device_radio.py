from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UniFiDevice, UniFiUsers, as_int


def discover_unifi_device_radio(
        section_unifi_device: UniFiDevice | None,
        section_unifi_device_users: UniFiUsers | None,
) -> DiscoveryResult:
    if section_unifi_device is None:
        return
    for radio in section_unifi_device.radio_table:
        if radio.value("name"):
            yield Service(item=str(radio.value("name")))


def check_unifi_device_radio(item: str, section_unifi_device: UniFiDevice | None, section_unifi_device_users: UniFiUsers | None) -> CheckResult:
    if section_unifi_device is None:
        return
    radio = next((entry for entry in section_unifi_device.radio_table if entry.value("name") == item), None)
    stats = next((entry for entry in section_unifi_device.radio_table_stats if entry.value("name") == item), None)
    if radio is None:
        return
    channel = as_int((stats or radio).value("channel"))
    frequency = "2.4 GHz" if channel and channel < 15 else "5 GHz"
    yield Result(state=State.OK, summary=f"Channel: {channel} ({frequency}), width: {radio.value('ht', 'unknown')} MHz")
    if stats:
        satisfaction = as_int(stats.value("satisfaction"))
        clients = as_int(stats.value("user-num_sta")) + as_int(stats.value("guest-num_sta"))
        yield Metric("unifi_channel", channel)
        yield Metric("unifi_satisfaction", satisfaction, boundaries=(0, 100))
        yield Metric("unifi_clients", clients)
        yield Result(state=State.OK, summary=f"Clients: {clients}, satisfaction: {satisfaction}%")
    if section_unifi_device_users:
        for user in section_unifi_device_users.root:
            if user.value("radio_name") == item:
                yield Result(state=State.OK, notice=f"Client: {user.hostname or user.name or user.value('mac', 'unknown')} ({user.ip or 'no IP'})")


check_plugin_unifi_device_radio = CheckPlugin(
    name="unifi_device_radio", service_name="UniFi Radio %s", sections=["unifi_device", "unifi_device_users"],
    discovery_function=discover_unifi_device_radio, check_function=check_unifi_device_radio,
)
