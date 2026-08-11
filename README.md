# UniFi special agent for Checkmk

This extension monitors a UniFi Network controller through its HTTPS API. It
creates controller and site services on the configured controller host and can
optionally create piggyback data for UniFi devices and clients. Piggyback data
can be used with Checkmk's dynamic host configuration to monitor the discovered
devices and clients as separate hosts.

## Requirements

- Checkmk 2.4 or later.
- Network access from the Checkmk site to the UniFi controller HTTPS port.
- A UniFi account that can read the controller, site, device, and client data.
- Automatic service discovery after enabling or changing this special agent.
- For piggyback targets, either preconfigured hosts with matching names or
  Checkmk dynamic host management for piggyback data.

## Configuration

Configure **UniFi connection parameters** in Setup.

| Option | Description |
| --- | --- |
| Use different Controller IP or DNS hostname | Optional. If empty, the primary IP address of the Checkmk host is used as the controller address. |
| Username / Password | Required UniFi API credentials. Passwords are stored using Checkmk's password store. |
| HTTPS port | Optional HTTPS port. The default is `443`. |
| Certificate validation | Enable **Disable certificate validation** only for controllers with a self-signed or otherwise untrusted certificate. When enabled, the agent passes `--no-cert-check` and does not validate the TLS certificate. |
| UDM-Pro API | Enable this for UDM-Pro/UniFi OS API endpoints. It switches authentication to `/api/auth/login` and API requests to `/proxy/network/api`. Leave it disabled for the old controller API. |
| Sites | Disabled means all sites are queried. Enable it and enter `all` explicitly if the setting should be visible in the rule, or provide one or more site descriptions to limit collection. Site descriptions must match the names shown by UniFi. |
| Device piggyback | Creates piggyback data for every returned UniFi device. |
| User piggyback | Creates a separate piggyback host for each client/user. Choose the naming scheme described below. |
| User piggyback on site host | Adds all users of a site to the site piggyback host. This is independent of **User piggyback**, so both modes can be enabled together. |

### Client piggyback naming

The **User piggyback** option has three mutually exclusive naming modes:

| Mode | Piggyback host name |
| --- | --- |
| IP | The UniFi client `ip` value, for example `192.168.18.112`. Users without an IP address are skipped. |
| Hostname | The UniFi client `hostname` value. Users without a hostname are skipped. |
| Hostname with Domain | The client hostname plus the configured domain, for example `win11xps.example.com`. A dot is added only when the hostname does not already end in that domain. Users without a hostname are skipped. |

The site-host option writes an `unifi_site_users` section below the site
piggyback host. The individual-user option writes an `unifi_user` section below
each client piggyback host. They do not replace one another.

## Created hosts and services

The service inventory depends on the data returned by the controller and on the
enabled piggyback options. Run service discovery after changing the rule.

### Controller host

The configured Checkmk host receives the following services:

| Service | Created when | State handling |
| --- | --- | --- |
| `UniFi Controller` | Always, if controller data is returned. | **WARN** when `unsupported_device_count` is greater than zero; otherwise **OK**. |
| `UniFi Site <site>` | For every site returned by the controller. | **WARN** when `num_new_alarms` is greater than zero; otherwise **OK**. |

The site service also shows the site ID plus the reported health subsystem,
status, user count, and guest count as details.

### Site piggyback host

For every selected site, the agent creates a piggyback target named after the
UniFi site description. It receives:

| Service | Created when | State handling |
| --- | --- | --- |
| `UniFi Controller` | Always for a selected site. | Same controller-state handling as above. |
| `UniFi Health <subsystem>` | For every health subsystem whose status is not `unknown`. | **OK** for `ok`, `healthy`, or `good`; any other status is **WARN**. A non-zero `num_pending` or `num_disconnected` is also **WARN**. |
| `UniFi Client <client>` | Only when **User piggyback on site host** is enabled. | **WARN** when the UniFi field `is_online` is false; otherwise **OK**. Missing `is_online` is treated as online. |

### Device piggyback host

With **Device piggyback** enabled, the agent creates one host for each UniFi
device. The host name is the device name. If the device has no name, the agent
uses `<model>-<last four serial characters>`.

| Service | Created when | State handling |
| --- | --- | --- |
| `UniFi Device` | Always on a device piggyback host. | Device state `1` (connected) is **OK**; state `2` (pending) is **WARN**; all other values are **CRIT**. A device not adopted is **WARN**. Reported `model_in_eol`, `model_in_lts`, or `model_incompatible` values are **WARN** when true. |
| `UniFi Environment` | The device reports `has_temperature` or `has_fan`. | Temperature is **CRIT** only when UniFi reports `overheating=true`. Fan level is informational. There is no numerical temperature or fan threshold. |
| `UniFi Interface <port>` | For every entry in the device `port_table`. | A port with `up=false` is **WARN**. A non-zero RX or TX error count is **WARN**. PoE is **WARN** when `poe_good=false`. |
| `UniFi Radio <radio>` | For every entry in the device `radio_table`. | Informational; no radio thresholds are applied. Connected client details are shown where UniFi supplies matching radio information. |
| `UniFi SSID <radio>_<SSID>` | For every entry in the device `vap_table`. | **WARN** when UniFi reports `up=false`; otherwise **OK**. |

### Individual user piggyback host

With **User piggyback** enabled, the agent creates one host per client using the
selected name scheme. Each host gets:

| Service | State handling |
| --- | --- |
| `UniFi Client Info` | Always **OK**. Shows hostname, UniFi name, IP address, network, and satisfaction. |
| `UniFi Client Uplink` | Always **OK**. Wired users show switch and port. Wireless users show access point, radio, signal, and noise. |

The user checks intentionally do not turn client signal, noise, or satisfaction
into WARN/CRIT states. These values are provided as metrics for graphing and
later analysis.

## Metrics and graphs

The extension exports the following metrics. Unless explicitly stated in the
service table, metrics have no built-in warning or critical levels.

| Metric | Unit | Emitted by |
| --- | --- | --- |
| `unifi_users` | count | Site and health services. |
| `unifi_guests` | count | Site and health services. |
| `unifi_clients` | count | Radio and SSID services. |
| `unifi_satisfaction` | percent, 0 to 100 | Device, interface, radio, site-user, and individual-user services. |
| `unifi_signal` | dBm | SSID and wireless individual-user services. |
| `unifi_noise` | dBm | Wireless individual-user services. |
| `unifi_temperature` | °C | Device environment service when a temperature is supplied. |
| `unifi_poe_power` | W | Interface services with PoE data. |
| `unifi_channel` | channel number | Radio services. |
| `unifi_if_rx_bytes` | bytes | Interface services. |
| `unifi_if_tx_bytes` | bytes | Interface services. |
| `unifi_if_rx_errors` | count | Interface services. A non-zero value makes the service WARN. |
| `unifi_if_tx_errors` | count | Interface services. A non-zero value makes the service WARN. |

Two graphs are supplied:

- **UniFi clients**: `unifi_users` and `unifi_guests`.
- **UniFi interface traffic**: `unifi_if_rx_bytes` and `unifi_if_tx_bytes`.

## Thresholds and rule sets

This extension currently provides only the special-agent connection rule. It
does not provide separate check-parameter rule sets for custom warning or
critical levels. The following levels are fixed by the plugin code:

- Unsupported controller devices: WARN above zero.
- New site alarms: WARN above zero.
- Site health: WARN for a status other than `ok`, `healthy`, or `good`.
- Pending or disconnected devices in site health: WARN above zero.
- Device connection state: OK for `1`, WARN for `2`, CRIT for every other
  state.
- Unadopted device, EOL/LTS/incompatible model: WARN when reported true.
- Interface down, RX/TX errors, or unhealthy PoE: WARN.
- Device overheating: CRIT when reported true.
- SSID down: WARN.
- Offline site-user: WARN.

No thresholds are applied to satisfaction, signal, noise, temperature, fan
level, PoE power, client counts, channels, or traffic values beyond the fixed
conditions listed above. To alert on such values, add a dedicated Checkmk rule
or extend the plug-in with check-parameter rules.

## Troubleshooting

- Verify the configured host, port, credentials, and UDM-Pro API setting.
- For TLS failures, install a trusted controller certificate or temporarily
  enable **Disable certificate validation**.
- Verify that selected site names match UniFi site descriptions exactly.
- Use `cmk -d <host>` to inspect the generated sections and piggyback headers.
- Ensure a target host name exactly matches the selected user/device piggyback
  name. Piggyback data is otherwise not assigned to that host.
- Repeat service discovery after enabling device or user piggyback options.

## License

Apache 2.0
