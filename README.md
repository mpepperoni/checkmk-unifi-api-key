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
   options.
5. Activate the changes.
6. Run service discovery on the controller host.
7. If you enabled piggyback data, also run service discovery on the generated
   site, device, or client hosts.

Run service discovery again after changing the selected sites, host naming
mode, piggyback options, or interface naming rules.

## Connection rule

The UniFi connection rule controls how the special agent connects and which
additional hosts it creates.

| Setting | Meaning |
| --- | --- |
| Hostname | DNS name or IP address of the UniFi controller. |
| Username and password | UniFi API credentials. |
| Port | HTTPS port of the controller. The default is `443`. |
| UDM Pro mode | Use this when a UniFi OS gateway needs the UDM-specific API endpoints. |
| Sites | Monitor all sites or only named sites. |
| Device piggyback | Write data for every managed UniFi device. |
| Site client piggyback | Write client data to each site piggyback host. |
| Individual client piggyback | Create one piggyback host per UniFi client. |
| Client host naming | Select IP address, hostname, or hostname plus domain for client hosts. |

TLS certificate validation is enabled by default. Disable it only when the
controller uses a self-signed certificate and the connection is on a trusted
network.

## Hosts and services

The controller host always receives controller services. Other hosts are
created only when their piggyback option is enabled.

| Host | Typical name | Purpose |
| --- | --- | --- |
| Controller | Your Checkmk controller host | Controller and site services |
| Site | UniFi site description | Client services for one site |
| Device | UniFi device name | Switch, access point, or gateway services |
| Client | Configured IP address or hostname | One client service per host |

Use stable and unique UniFi site and device names. These names are used as
piggyback host names.

Typical device services include **UniFi Device**, **UniFi Environment**,
**UniFi Radio**, **UniFi SSID**, **Unifi Interface _port_**, and **Unifi PoE
budget**. The exact list depends on the device type and its reported data.

## Switch interfaces

The interface check is named `unifi_interfaces`. It uses the existing
`unifi_device_if` agent section, so no change to the agent output is needed.

UniFi ports are passed to Checkmk's standard interface implementation. This
means that standard Checkmk interface rules, thresholds, metrics, and graphs
also apply to UniFi interfaces.

| Checkmk interface property | UniFi source |
| --- | --- |
| Index | `port_idx` |
| Description | `Port <port_idx>` |
| Alias | Port `name` |
| Administrative state | `enabled`, or `enable` when needed |
| Operational state | `up` |
| Speed | `speed`, converted from Mbit/s to bit/s |

### Service discovery and service names

Use the standard Checkmk **Switch port discovery** / interface discovery rules
to choose which ports become services and how they are named. The normal
default behaviour is preserved: ports that are operationally down are not
discovered unless a matching rule explicitly includes them.

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

The service also adds UniFi-specific information, such as jumbo-frame status,
satisfaction, and PoE details. If PoE is enabled for a port, Checkmk reports
the PoE mode, class, power in W, voltage in V, and current in mA. A failed
`poe_good` value remains a warning.

## PoE budget

The **Unifi PoE budget** service is created when a device reports total used
PoE power. It displays:

- Total used PoE power
- Maximum PoE power, when reported
- Maximum effective PoE power, when reported
- PoE budget usage as a percentage when a usable maximum is available

The **UniFi PoE budget levels** rule has two independent optional upper limits:

- **Upper total PoE power usage**: values in W; disabled by default.
- **Upper total PoE budget usage**: values in percent; WARN at 95% and CRIT at
  98% by default.

The percentage uses the reported maximum power. If only the effective maximum
is available, it is used instead.

## Hardware and network inventory

The extension can store device and port information in Checkmk's Hardware/
Software Inventory.

| Inventory path | Contents |
| --- | --- |
| `hardware` / `software` | Device type, model, serial number, and firmware data when reported. |
| `networking/interfaces` | Standard interface data: index, description, alias, speed, admin state, and operational state. Duplex is empty for a down port. |
| `networking/unifi_switch_ports` | UniFi-specific port configuration such as STP, autonegotiation, forwarding mode, 802.1X, and network assignment. |
| `networking/unifi_interfaces_poe` | Per-port PoE capability, enable state, mode, class, description, and alias. |

### Avoid duplicate interface inventory

If the same switch is also inventorized through SNMP, both data sources can
write entries under `networking/interfaces`. To avoid duplicate or conflicting
entries, use the **UniFi interface inventory** rule and clear **Enable UniFi
interface inventory** for that host. It is enabled by default.

This only disables the standard UniFi interface inventory table. It does not
disable SNMP inventory, monitoring services, the UniFi-specific switch-port
inventory, or the UniFi PoE inventory table.

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

## Security notes

Keep TLS certificate validation enabled whenever possible. If a self-signed
certificate requires disabling validation, use a trusted network path. Limit
the UniFi account to read-only access and store its password only in Checkmk's
rule configuration.

## License

See the license information included with this extension.
