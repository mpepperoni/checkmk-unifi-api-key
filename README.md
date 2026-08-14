# UniFi special agent for Checkmk

This extension lets Checkmk collect monitoring data from a UniFi Network
controller. It is useful when the controller manages switches, access points,
gateways, and connected clients.

The extension connects to the controller over HTTPS. It then writes data for
the controller itself and, if configured, piggyback data for UniFi sites,
devices, and clients. A *piggyback host* is a normal Checkmk host that receives
data from another host; in this case, the controller is the data source.

The documentation uses simple network terms. You only need basic knowledge of
IP addresses, HTTPS, switch ports, and Checkmk service discovery to get
started.

## What the extension monitors

Depending on the selected UniFi features and the data supplied by the
controller, the extension can create services for:

- Controller state, sites, and controller health
- UniFi devices, including adoption state and device information
- Switch interfaces, traffic, errors, discards, broadcast and multicast packets
- PoE status and PoE power budget on switches
- Access-point radio, SSID, temperature, signal, and noise information
- Connected clients, either on a site host or on separate client hosts

Not every UniFi model reports every value. Missing data is normal for devices
without a feature, for example a switch without PoE or an access point without
a temperature sensor.

## Requirements

- Checkmk 2.4.0p19 or later
- Network access from the Checkmk site to the UniFi controller HTTPS port
  (normally `443`)
- A UniFi account that can read the selected sites, devices, and clients

Use a dedicated read-only UniFi account when possible. The extension does not
need permission to change controller settings.

## Installation and first setup

1. Install the extension in the Checkmk site.
2. Create a Checkmk host for the UniFi controller.
3. Open **Setup > Agents > Other integrations > UniFi connection parameters**.
4. Create a rule for the controller host and enter its address, credentials, and
   options. The account needs read access to every selected site.
5. Activate the changes.
6. Run service discovery on the controller host.
7. If you enabled piggyback data, create matching Checkmk hosts and run service
   discovery on them.

Piggyback output does not create Checkmk hosts automatically. Run service
discovery again after changing the selected sites, host naming mode, piggyback
options, or interface naming rules.

## Connection rule

The UniFi connection rule controls how the special agent connects and which
additional hosts it creates.

| Setting | Meaning |
| --- | --- |
| Hostname | DNS name or IP address of the UniFi controller. |
| Username and password | UniFi API credentials. |
| Port | HTTPS port of the controller. The default is `443`. |
| UDM Pro mode | Use this when a UniFi OS gateway needs the UDM-specific API endpoints. |
| Sites | Monitor all sites or only named sites. Names are the displayed UniFi site descriptions, not internal site IDs, and matching is case-sensitive. An unset list queries all sites; use `all` to make this setting explicit. |
| Device piggyback | Write data for every managed UniFi device. |
| Site client piggyback | Write client data to each site piggyback host. |
| Individual client piggyback | Create one piggyback host per UniFi client. |
| Client host naming | Select IP address, hostname, or hostname plus domain for client hosts. A client without the selected value is skipped. In hostname-plus-domain mode, an existing matching domain is not appended twice. |

TLS certificate validation is enabled by default. Disable it only when the
controller uses a self-signed certificate and the connection is on a trusted
network.

## Hosts and services

The controller host always receives controller services. The agent always
writes data for selected site names; device and individual-client data are
optional. Create the Checkmk hosts yourself with exactly the piggyback names;
the agent does not create host objects.

| Host | Typical name | Purpose |
| --- | --- | --- |
| Controller | Your Checkmk controller host | Controller and site services |
| Site | UniFi site description | Site-specific controller and health services; client services when enabled |
| Device | UniFi device name | Switch, access point, or gateway services |
| Client | Configured IP address or hostname | One client service per host |

Use stable and unique UniFi site and device names. These names are used as
piggyback host names. Duplicate site descriptions, device names, or client
names cause data to be written to the same piggyback host and can mix services.
IP-based client names are usually unique but can change with DHCP.

Typical device services include **UniFi Device**, **UniFi Environment**,
**UniFi Radio**, **UniFi SSID**, **Unifi Interface _port_**, **Unifi PoE
Interface _port_**, and **Unifi PoE budget**. The exact list depends on the
device type and its reported data.

## Service states, metrics, and built-in thresholds

The following states are fixed in the extension. They do not have a separate
UniFi rule unless a rule is named below.

| Service | State behaviour | Metrics and notes |
| --- | --- | --- |
| **UniFi Controller** | WARN when the controller reports one or more unsupported devices; otherwise OK. | Name, type, build, and unsupported model list are informational. |
| **Unifi Site _site_** | WARN when `num_new_alarms` is greater than zero; otherwise OK. | User and guest counts can be emitted once for every controller health subsystem. |
| **UniFi Health _subsystem_** | OK only for status `ok`, `healthy`, or `good`; any other reported status is WARN. Non-zero pending or disconnected device counts are WARN. | A subsystem with status `unknown` is not discovered. |
| **UniFi Device** | `connected` is OK, `pending` is WARN, `disconnected` or unknown is CRIT. Not adopted is WARN. Reported EOL, LTS, or incompatible model flags are WARN. | Satisfaction is a 0–100% metric without default alert levels. Both numeric and textual API states are accepted. |
| **UniFi Environment** | Reported overheating is CRIT. Fan level is informational. | Temperature in °C; no numeric temperature levels are configured. |
| **UniFi Radio _radio_** | Informational (OK). | Channel, client count, and satisfaction; no radio thresholds. |
| **UniFi SSID _interface_\_SSID_** | WARN when the VAP is down; otherwise OK. | Client count and average signal in dBm. |
| **UniFi Client _client_** on a site host | WARN when UniFi reports `is_online=false`; otherwise OK. | Satisfaction 0–100%. Mobile clients can therefore create expected warnings. |
| **UniFi Client Info/Uplink** on a client host | Informational (OK). | Satisfaction; wireless signal/noise, or wired switch and port. |

The API request timeout is 20 seconds per request. The agent requests controller
information and the site list, then devices, clients, health, and controller
information for every selected site. Large installations or unreachable sites
can therefore make the check slow. A failed required API request stops the
agent run.

## Switch interfaces

The interface check is named `unifi_interfaces`. It uses the existing
`unifi_device_if` agent section, so no change to the agent output is needed.

UniFi ports are passed to Checkmk's standard interface implementation. This
means that standard Checkmk interface rules, thresholds, metrics, and graphs
also apply to UniFi interfaces.

## LLDP neighbors

For every device piggyback host, the agent emits a compact `unifi_device_lldp`
section directly from the controller's `lldp_table`. This preserves LLDP data
for access points whose `port_table` is empty. When the remote chassis MAC
matches another managed UniFi device in the same site, the section also carries
its name, model, management IP address, and type. The inventory is shown under
`networking/lldp_neighbors`.

| LLDP column | Value |
| --- | --- |
| Local Port | `Port <local_port_idx>` |
| Neighbor Port | The resolved remote port index as `Port <port_idx>`; otherwise the LLDP `port_id`. |
| Port Description | The remote UniFi port alias, if available; otherwise the LLDP `port_id`. |
| System Description | Model name from `DEVICE_MODELS`, followed by the UniFi model code in parentheses. If the model is unknown to the mapping, only the model code is shown. |

The remote port index and alias can only be resolved for managed UniFi devices
in the same selected site. Third-party or otherwise unknown LLDP neighbors
retain the values supplied by LLDP.

For a link aggregation group, UniFi exposes only the first member through its
normal uplink field. The agent therefore pairs the sorted, reciprocal LLDP
entries of a managed LAG, so each physical member retains its matching remote
port (for example, local ports 51/52 map to remote ports 9/10).

### Service discovery and service names

Use the standard Checkmk **Switch port discovery** / interface discovery rules
to choose which ports become services and how they are named. The normal
default behaviour is preserved: operationally up Ethernet ports (interface
type `6`) are discovered. Ports that are operationally down are not discovered
unless a matching rule explicitly includes them.

The naming options match standard interfaces:

- **Index** uses the UniFi port number.
- **Description** uses `Port <number>`.
- **Alias** uses the configured UniFi port name.
- The option to pad port numbers with leading zeroes is honoured.

After changing a discovery rule, run service discovery again. Existing services
are not automatically renamed.

### Interface results and graphs

Traffic counters, packet counters, errors, discards, broadcasts, and multicasts
are handed to the Checkmk interface library. As a result, Checkmk's normal
interface metrics and graphs are used instead of custom copies.

The service also adds UniFi-specific information, such as jumbo-frame status
and satisfaction. PoE values are reported by the separate **Unifi PoE
Interface _port_** service.

The complete built-in Checkmk **Network interfaces** rule applies to this
service. Its default error-rate level for errors in both directions is WARN at
**0.01%** and CRIT at **0.1%**. The normal built-in options for expected state
and speed, traffic, packet/error/discard levels, averaging, and interface
groups are available as well. Configure them with the standard interface rule,
not a UniFi-specific rule.

### PoE interface services

The `unifi_poe_interfaces` check uses the same `unifi_device_if` agent section
and exactly the same **Switch port discovery** rules as `unifi_interfaces`.
It discovers one **Unifi PoE Interface _port_** service only where UniFi
reports `port_poe=true` and the port matches the discovery rule. The item name,
including index, description, alias, duplicate-name handling, and port-number
padding, is therefore identical to the matching **Unifi Interface _port_**
service. By default, operationally down PoE ports are not discovered.

It reports the PoE mode, output state, detected class, voltage, current, and
power. The current power is also displayed as a service Perf-O-Meter with a
0–100 W focus range. A disabled output is OK. An enabled but down port has no PoE state,
voltage, current, or power result. A powered port with `poe_good=false` is
WARN, except for the reported `pasv24` mode, which is shown as permanent 24 V.
The built-in voltage limits depend on the reported class: classes 0–3 use
44.2/44.0 V lower WARN/CRIT and 56.8/57.0 V upper WARN/CRIT; classes 4–6 use
50.2/50.0 V lower WARN/CRIT and the same upper limits; classes 7–8 use
52.2/52.0 V lower WARN/CRIT and the same upper limits. Voltage uses
`notice_only`, so these levels are shown as notices and do not change the
service state. Current and power have no default levels.

## PoE budget

The **Unifi PoE budget** service is created when a device reports total used
PoE power, including `0 W`. It displays:

- Total used PoE power
- Maximum PoE power, when reported
- Maximum effective PoE power, when reported
- PoE budget usage as a percentage when a usable maximum is available

The **UniFi PoE budget levels** rule has two independent optional upper limits:

- **Upper total PoE power usage**: values in W; disabled by default.
- **Upper total PoE budget usage**: values in percent; WARN at 95% and CRIT at
  98% by default.

The percentage uses the reported maximum power. If only the effective maximum
is available, it is used instead. If no positive maximum is available, the
percentage cannot be calculated and no percentage threshold is evaluated.

The used, maximum, effective maximum, and percentage values are metrics. The
maximum values are emitted when the controller provides them, so the supplied
PoE budget graph can show the available budget as well as usage.

## Rules used by this extension

The extension provides these rules:

| Rule | Scope | Default |
| --- | --- | --- |
| **UniFi connection parameters** | Controller host | HTTPS port `443`, certificate validation enabled, legacy API, all sites, and all piggyback options disabled. |
| **UniFi PoE budget levels** | **Unifi PoE budget** | Total W limit disabled; percentage WARN `95%`, CRIT `98%`. |
| **UniFi inventory** | Device inventory | Interface and LLDP inventory enabled. |

It also uses two built-in Checkmk rule sets:

| Built-in rule | Used for | Relevant default |
| --- | --- | --- |
| **Switch port discovery** (`inventory_if_rules`) | Discovering and naming **Unifi Interface** services | Up Ethernet ports only; item is the port index; port numbers are padded with leading zeroes. |
| **Network interfaces** (`interfaces`) | Checking **Unifi Interface** services | Error rate in both directions: WARN `0.01%`, CRIT `0.1%`. All other normal interface parameters remain available. |

Changing a switch-port naming option or its matching conditions requires a new
service discovery. Existing services are not renamed automatically. Alias
naming uses the configured UniFi port name and can be ambiguous if names are
not unique.

## Hardware and network inventory

The extension can store device and port information in Checkmk's Hardware/
Software Inventory.

| Inventory path | Contents |
| --- | --- |
| `hardware` / `software` | Device type, model, serial number, and firmware data when reported. |
| `networking/interfaces` | Standard interface data: index, description, alias, speed, admin state, and operational state. Duplex is empty for a down port. |
| `networking/lldp_neighbors` | LLDP neighbor identity, remote port, remote port alias, management address, and model description. |
| `networking/unifi_switch_ports` | UniFi-specific port configuration such as STP, autonegotiation, forwarding mode, 802.1X, and network assignment. |
| `networking/unifi_interfaces_poe` | Per-port PoE capability, enable state, mode, class, description, and alias. |

### Avoid duplicate interface inventory

If the same switch is also inventorized through SNMP, both data sources can
write entries under `networking/interfaces` and `networking/lldp_neighbors`.
Use the **UniFi inventory** rule to choose the affected tables independently:

- Clear **Enable UniFi interface inventory** to suppress only the standard
  `networking/interfaces` inventory.
- Clear **Enable UniFi LLDP inventory** to suppress only the standard
  `networking/lldp_neighbors` inventory.

Both options are enabled by default. They do not disable SNMP inventory,
monitoring services, the UniFi-specific switch-port inventory, or the UniFi
PoE inventory table.

### PoE inventory values

The PoE inventory table uses readable values such as `Yes`/`No`, `Auto`,
`24V Passive`, and `Class 3`. The Checkmk 2.5 inventory user interface provides
selectable filters for these fields. If a newer controller reports an unknown
PoE mode, class, or capability value, the raw value is kept in the inventory.

## Clients

With site client piggyback enabled, each site host can receive one service per
client. With individual client piggyback enabled, each client receives its own
host. Client information can include IP address, MAC address, connection state,
and wired or wireless connection details when UniFi provides them.

An offline client may produce a warning. This is useful for important devices,
but can create noise for mobile devices that often leave the network.

## Troubleshooting

### No services are found

- Check the controller address, port, username, and password in the connection
  rule.
- Verify that the Checkmk site can reach the controller via HTTPS.
- Confirm that the UniFi account can read the selected sites.
- Activate changes and run service discovery again.

### A device, site, or client host is missing

- Enable the matching piggyback option in the connection rule.
- Create a Checkmk host whose name exactly matches the piggyback name. The
  special agent writes data but does not create hosts.
- Check that the UniFi site or device name is unique.
- Run discovery on the controller host first, then on the piggyback host.

### A switch port is missing

- Check the standard interface discovery rules.
- By default, only operationally up ports are discovered.
- Add or adjust a rule if down ports, a specific port type, or another naming
  scheme should be included.
- Run service discovery after changing the rule.

### Interface graphs show technical names

The extension uses Checkmk's standard interface metric names. After updating
the extension, activate changes and wait for new monitoring data. Historical
graph data can retain older metric names until it expires.

### The check takes too long or fails completely

- Each API request times out after 20 seconds. Four requests are needed for
  every selected site, in addition to the controller and site-list requests.
- Verify the selected site names. They must be the visible UniFi site
  descriptions and are case-sensitive.
- Check controller reachability, account rights, API mode, and TLS validation.
  One failed required request ends the complete agent run.

## Security notes

Keep TLS certificate validation enabled whenever possible. If a self-signed
certificate requires disabling validation, use a trusted network path. Limit
the UniFi account to read-only access and store its password only in Checkmk's
rule configuration.

## License

See the license information included with this extension.
