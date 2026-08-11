# UniFi special agent for Checkmk

This extension connects Checkmk to a UniFi Network controller. It collects controller, site, device, switch-port, Wi-Fi and client information and creates services on suitable Checkmk hosts.

The agent supports both a self-hosted UniFi Network application and UniFi gateways such as UDM Pro.

## Requirements

- Checkmk 2.4.0p19 or newer
- Network access from the Checkmk site to the UniFi controller HTTPS port (default: `443`)
- A UniFi account that can read the selected sites, devices and clients

## Installation and first setup

1. Install the extension in the Checkmk site.
2. Create a Checkmk host for the UniFi controller.
3. Open **Setup > Agents > Other integrations > UniFi connection parameters**.
4. Create a rule for the controller host and enter the connection details.
5. Run a service discovery on the controller host and on the piggyback hosts created by the agent.

When you change the selected sites, the host naming mode, or interface naming rules, run service discovery again.

## Connection options

| Option | Description |
| --- | --- |
| Hostname | DNS name or IP address of the UniFi controller. |
| Username and password | Credentials for the UniFi Network API. |
| Port | HTTPS port of the controller. The default is `443`. |
| UDM Pro mode | Enable this for UniFi OS gateways when required by the controller API. |
| Sites | Monitor all sites or only selected sites. |
| Device piggyback | Create a Checkmk piggyback host for every UniFi device. |
| Site client piggyback | Create client services on each site piggyback host. |
| Individual client piggyback | Create a separate piggyback host for every UniFi client. |
| Client host naming | Use the client IP address, hostname, or hostname plus domain. |

TLS certificate validation is enabled by default. The connection rule can disable it for controllers with a self-signed certificate. Enable this option only when you trust the network path and the controller.

## Hosts created by the agent

The controller host always receives controller services. Depending on the rule, the special agent also writes piggyback data for sites, devices and individual clients.

| Host type | Host name | Created when |
| --- | --- | --- |
| Controller | The Checkmk host running the special agent | Always |
| Site | UniFi site description | For every selected site |
| Device | UniFi device name | Device piggyback is enabled |
| Client | IP address or hostname, based on the rule | Individual client piggyback is enabled |

Use stable and unique UniFi site and device names. These names are used as piggyback host names.

## Controller services

The controller host receives the following services:

- **UniFi Controller**: Basic controller information and the number of unsupported devices. Unsupported devices cause a warning.
- **Unifi Site _site_**: State and basic statistics for each selected site.
- **UniFi Health _site_**: Health values reported by the controller. Unhealthy subsystems, pending devices or disconnected devices create a warning.

## Site client services

If site client piggyback is enabled, each site host receives one service per client:

- **UniFi Client _client_**: Client name, IP address, MAC address and connection status.

An offline client creates a warning. This is useful when the client should normally be online. If many clients are intentionally intermittent, consider limiting service discovery or using individual client hosts only for important devices.

## Device services

With device piggyback enabled, the agent creates device hosts. Typical services are:

- **UniFi Device**: Adoption state, device state and basic device details.
- **UniFi Environment**: Temperature and overheating information when the controller provides it.
- **UniFi Radio**: Radio configuration and status for access points.
- **UniFi SSID**: SSID availability for access points.
- **Unifi Interface _port_**: Switch-port state, traffic and port details.
- **UniFi PoE budget**: Total PoE consumption and the reported PoE budget, when the device reports PoE power data.

Device adoption problems create warnings. A device state reported as failed creates a critical state. An overheating environment state is critical.

## Switch interfaces

The interface check is registered as `unifi_interfaces`, but it keeps the existing UniFi agent section. No change to the agent output is required.

The check uses Checkmk's standard interface discovery and the standard interface ruleset. This means that common interface settings, thresholds and graph behaviour work like they do for normal SNMP interface checks.

For every UniFi port, the data is mapped as follows:

| Checkmk interface field | UniFi value |
| --- | --- |
| Index | `port_idx` |
| Description | `Port <port_idx>` |
| Alias | Port `name` from UniFi |
| Administrative state | `enabled` or `enable` |
| Operational state | `up` |
| Speed | `speed`, converted from Mbit/s to bit/s |

The interface service name is chosen by the standard Checkmk interface discovery rules. For example, you can use the port index, the description (`Port 8`) or the UniFi port name. The rule option for leading zeroes is also honoured.

The check passes traffic, packet and error counters to Checkmk's standard interface implementation. Therefore the normal interface graphs and labels are used for bandwidth, packets, errors, discards, broadcasts and multicasts.

### PoE information

For an enabled PoE port, the interface service also shows:

- PoE mode and PoE class
- PoE enabled state
- PoE health (`poe_good`); a failed PoE health state remains a warning
- PoE power in W
- PoE voltage in V
- PoE current in mA

Power, voltage and current are emitted as metrics through `check_levels`. They are available for graphing and can be controlled with Checkmk threshold rules where applicable. A port without enabled PoE reports an informational message only.

### Device PoE budget

The **UniFi PoE budget** service is discovered when the UniFi device reports total PoE usage. It shows and stores these values:

- Total PoE power used
- Maximum PoE power
- Maximum effective PoE power
- PoE budget usage in percent: `total_used_power / total_max_power`

The check has two independent optional upper-level settings in **UniFi PoE budget levels**:

- **Upper total PoE power usage**: Thresholds in W. Disabled by default.
- **Upper total PoE budget usage**: Thresholds in percent. Defaults to WARN at 95% and CRIT at 98%.

If the controller does not report `total_max_power`, the service still shows the available power values but cannot calculate the percentage. It becomes UNKNOWN so that the missing budget information is visible.

## Hardware and network inventory

The extension writes hardware and network inventory data for device piggyback hosts.

- **Hardware / System**: Manufacturer, device model, serial number, device name and device type.
- **Software / Operating system**: UniFi firmware version and device type.
- **Networking / Interfaces**: Standard Checkmk interface inventory with index, description, alias, administrative and operational state, speed and Ethernet port type.
- **Networking / UniFi switch ports**: UniFi-specific port configuration, such as autonegotiation, duplex, STP, PoE capability, 802.1X and network assignment.

UniFi does not provide every IF-MIB value in the used API response. In particular, the extension does not invent a switch-port MAC address, resolved VLAN ID, or LLDP/CDP neighbour when the controller has not supplied it.

## Individual client services

When individual client piggyback is enabled, Checkmk creates one host for each client. The host name is configured in the connection rule.

Client hosts receive connection details. Wired clients show the connected switch and port when the controller provides the information. Wireless clients show the access point, radio, signal and noise values.

## Metrics and graphs

The extension uses Checkmk's built-in interface metrics and graphs for switch traffic and interface counters. It does not create custom traffic graphs for these values.

The following UniFi-specific metrics are provided when the matching data is available:

- Client counts and guest counts
- Client satisfaction
- Wi-Fi signal, noise and channel
- Device temperature
- PoE power, voltage and current
- Total PoE power used, total budget, effective budget and budget usage

PoE port values and PoE budget values have dedicated graphs. Other values use their matching Checkmk metric definitions.

## Troubleshooting

### No services are discovered

- Verify the controller hostname, port and credentials in the UniFi connection rule.
- Check that the Checkmk site can reach the controller over HTTPS.
- Verify that the configured UniFi account can access the selected sites.
- Run service discovery after enabling piggyback options or changing the selected sites.

### Device or site hosts are missing

- Enable the corresponding device, site client or individual client piggyback option.
- Check that site descriptions and device names are unique and valid Checkmk host names.
- Run service discovery on the controller host first, then on the created piggyback hosts.

### Interface services have unexpected names

- Open the standard interface discovery rules in Checkmk.
- Select the desired naming scheme: index, description or alias.
- Run service discovery again after changing the naming rule.

### Interface graphs show technical metric names

The interface check translates its legacy counter names to Checkmk's standard interface metrics. After installing or updating the extension, reload the Checkmk configuration and allow new monitoring data to arrive. Existing graph data may retain old names until its retention period ends.

## Security notes

Create a dedicated UniFi account with read-only access where possible. Store credentials only in the Checkmk rule configuration and limit network access to the UniFi controller. Keep TLS certificate validation enabled whenever possible. If it must be disabled for a self-signed certificate, use a trusted network path and suitable network controls.

## License

See the license information included with this extension.
