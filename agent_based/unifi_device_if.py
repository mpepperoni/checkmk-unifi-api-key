from cmk.agent_based.v2 import CheckPlugin, CheckResult, DiscoveryResult, Metric, Result, Service, State
from .unifi import UniFiInterfaces, UniFiObject, as_float, as_int


def _item(port: UniFiObject) -> str:
    return str(port.value("port_idx", port.value("name", "unknown")))


def _port(item: str, section: UniFiInterfaces) -> UniFiObject | None:
    return next((port for port in section.root if _item(port) == item), None)


def discover_unifi_device_if(section: UniFiInterfaces) -> DiscoveryResult:
    for port in section.root:
        yield Service(item=_item(port))


def check_unifi_device_if(item: str, section: UniFiInterfaces) -> CheckResult:
    port = _port(item, section)
    if port is None:
        return
    up = bool(port.value("up"))
    name = port.value("name", item)
    speed = as_int(port.value("speed"))
    yield Result(state=State.OK if up else State.WARN, summary=f"{name}: {'up' if up else 'down'}")
    yield Result(state=State.OK, summary=f"Speed: {speed} Mbit/s")
    for key, metric, label in (("rx_bytes", "unifi_if_rx_bytes", "RX bytes"), ("tx_bytes", "unifi_if_tx_bytes", "TX bytes"), ("rx_errors", "unifi_if_rx_errors", "RX errors"), ("tx_errors", "unifi_if_tx_errors", "TX errors")):
        value = as_int(port.value(key))
        yield Metric(metric, value)
        if key.endswith("errors"):
            yield Result(state=State.WARN if value else State.OK, notice=f"{label}: {value}")
    satisfaction = as_int(port.value("satisfaction"))
    if up and satisfaction:
        yield Metric("unifi_satisfaction", satisfaction, boundaries=(0, 100))
        yield Result(state=State.OK, summary=f"Satisfaction: {satisfaction}%")
    if port.value("portconf"):
        yield Result(state=State.OK, notice=f"Network: {port.value('portconf')}")
    yield Result(state=State.OK, notice=f"Jumbo frames: {'enabled' if port.value('jumbo') else 'disabled'}")
    if port.value("port_poe"):
        poe_power = as_float(port.value("poe_power"))
        yield Metric("unifi_poe_power", poe_power)
        yield Result(state=State.OK if port.value("poe_good", True) else State.WARN, notice=f"PoE: {port.value('poe_mode', 'unknown')}, {poe_power:.2f} W")


check_plugin_unifi_device_if = CheckPlugin(
    name="unifi_device_if", service_name="UniFi Interface %s", sections=["unifi_device_if"],
    discovery_function=discover_unifi_device_if, check_function=check_unifi_device_if,
)
