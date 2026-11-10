# Local API-key backend: pilot installation

This fork adds a local Network Integration API backend to the GitLab UniFi
extension. Target: Checkmk 2.5.0p18, UniFi OS 5.1.35, Network 10.6.109.
The official 10.6.109 OpenAPI contract was inspected; no live controller or
native Checkmk runtime was available during development. Treat this as a pilot
package until the staging steps below pass. OS 6 compatibility is not yet tested.

Source baseline: checkmk-extensions/unifi commit
`5c89ea877336c9ca738533bbcda4c2c2429a8f5a` (Apache-2.0).
API contract: https://developer.ui.com/network/v10.6.109/openapi.json

## Install

1. Back up your Checkmk site and retain the currently installed UniFi MKP.
   Install first on a staging site running 2.5.0p18.
2. Build with `python3 tools/build_mkp.py`, or use the supplied MKP in `dist/`.
3. Use Setup > Maintenance > Extension packages to upload and enable the MKP.
   Its package name is `unifi`; it replaces the upstream implementation and
   must not coexist with another package owning the same `plugins/unifi` files.
   If your current extension has another package name, resolve file ownership
   before enabling this package. LINET is a separate implementation: avoid
   collecting the same device through both plugins during migration.
4. In UniFi Network on the local console, open Integrations and generate a local
   API key. Use the least permissions the console offers for these reads; the
   collector performs only GET requests. Do not use a Site Manager cloud key.
5. Save the key in the Checkmk password store. Restrict access to its consumers.
6. In Setup > Agents > Other integrations > UniFi connection parameters:
   - Controller hostname/IP and HTTPS port: local console, normally port 443.
   - Select **Local Network Integration API key**, referencing the stored key.
   - Remove **Username**, **Password**, **UDM-Pro API**, and both legacy client
     piggyback options. Conflicting combinations are rejected during validation.
   - Enable **Device piggyback** for per-device services.
   - Keep certificate validation enabled and trust your console's issuing CA.
7. Sites defaults to `all`: this queries all sites returned by THIS Network
   application, not necessarily your entire fabric. For production, prefer an
   explicit list of site UUIDs. Exact display names and legacy internal
   references also work. Unknown configured sites cause collection to fail.
8. Activate changes and run discovery on the controller host. Expect
   `UniFi API Application` and one `UniFi API <site UUID>` service per site.
9. Device piggyback names are `unifi-` plus the MAC without colons, lower case,
   for example `unifi-aabbccddeeff`. Create matching piggyback-only hosts and run
   discovery. Device services include Device, Statistics and reported ports.
   Automatic host creation requires your normal DCD configuration.

Using the same physical MAC preserves host identity across device renames and
site/console moves. Do not monitor a moving device from two active collectors:
piggyback streams from multiple sources must be reconciled. Repeated device
names are safe. Existing legacy name-based hosts are not automatically renamed;
plan host/history migration before switching an existing deployment.

## Monitoring coverage

- Controller API reachability, application version, per-site device state and
  connected-client count.
- Device identity, firmware, adoption/connection state and connected-client count.
- Available uptime, CPU/memory utilization, load averages and uplink rates.
- Reported port link state/speed and PoE state/standard.
- Device hostnames use stable MAC identities; site services use UUIDs.

Per-port traffic/error/discard counters, PoE wattage/budgets, temperatures,
legacy satisfaction/health and radio/SSID services are not implemented in this
backend. Add SNMP independently for supported device/interface metrics.
Individual client hosts and legacy site-client piggyback are not supported;
client counts are collected per site and device.

Missing statistics never become zero. Offline devices retain their availability
service and report unavailable statistics. Unsupported detail/statistics
endpoints (404/405/501) produce a warning; authentication failures and other
HTTP/transport errors fail collection. No fallback to password login occurs.
Link DOWN is informational because the API does not establish whether a port is
expected to be connected. PoE LIMITED is WARN. CPU/memory are graphed without
threshold alerts in this initial release.

## Multi-site fabric and polling

Configure one collection target per managing console if the first console's
`/v1/sites` list does not cover every required site. Local API keys and UUIDs
belong to the relevant console/application. The backend does not discover
other fabric consoles or contact UniFi cloud.

The collector paginates sites, devices and clients. It requests device details
and requests statistics for ONLINE devices, sequentially, with a 20-second
per-request timeout. Approximately `1 + site pages + device/client pages +
N device-detail requests + M online-device-statistics requests` per poll.
Start with one site, measure execution time, and use a Checkmk special-agent
execution interval appropriate for the device count. This version has no
persistent cache or concurrent requests. It fails on HTTP 429 rather than
retrying indefinitely. No partial inventory is emitted on failed collection.

## Required live acceptance checks

1. Confirm native Checkmk ruleset loading, password reference rendering and
   plugin loading on 2.5.0p18; enable/discover one selected site.
2. Confirm returned site UUIDs cover the expected fabric scope. Add other
   managing consoles if required.
3. Compare device states, client counts, uptime and port/PoE state against UniFi.
   Confirm uplink rate units against the controller before relying on graphs.
4. Check piggyback host mapping, duplicate display names, renamed devices,
   unplugged devices, and devices with missing optional statistics.
5. Revoke a test key and verify a datasource failure without credential leakage.
   Check unknown sites, bad certificates and insufficient key permissions.
6. Measure full-site polling time and ensure checks do not overlap.
7. Confirm old username/password rules still collect successfully.
8. Repeat these checks after Network upgrades and before migrating to UniFi OS 6.

## Development and rollback

Tests: `python -m pytest -q` with requests, pydantic v2 and pytest installed.
Unit tests use API response fixtures and small Checkmk API stand-ins. They do
not substitute for native Checkmk or live controller acceptance tests.

Existing login rules keep their stored schema and legacy collector. API-key
rules use dedicated sections/checks so incomplete public data cannot trigger
legacy defaults. Switching back requires restoring the old rule credentials
and rediscovering services. To roll back code, disable this MKP and restore the
previous package through Checkmk's package manager. Keep a site backup for
restoring package/rule state if necessary.

## Community Edition: export the device hosts as CSV

Community Edition does not provide DCD automatic host creation. The standalone
`tools/export_unifi_hosts.py` helper converts the controller's existing special
agent output into a semicolon-separated `hostname;alias` CSV. It needs Python 3
only and works with the initial API-key package, so upgrading the MKP is optional.
It does not contact UniFi or need API keys. Offline devices are included.

1. Enable **Device piggyback** in the controller's UniFi connection rule and
   activate changes. Run a check on the controller host.
2. Copy `tools/export_unifi_hosts.py` to the Checkmk server. As the Checkmk site
   user, substitute the existing Checkmk CONTROLLER HOST NAME below (not its IP):

   ```bash
   set -o pipefail
   cmk -d CONTROLLER_HOST | python3 export_unifi_hosts.py > unifi-hosts.csv
   head -n 3 unifi-hosts.csv
   wc -l unifi-hosts.csv
   ```

   The exporter writes the device count to stderr, leaving stdout as CSV only.
   For 200 devices the CSV has 201 lines, including its header. Do not import if
   the pipeline reports an error. To avoid another controller collection, a
   saved `cmk -d` output file can be supplied as the script's positional argument.
   Normal monitoring runs never write CSV files or change host configuration.

   With the updated MKP, the same helper is installed as
   `~/local/lib/python3/cmk_addons/plugins/unifi/libexec/unifi_hosts_csv` and can
   be called through Python using that path instead of `export_unifi_hosts.py`.

3. Create a dedicated UniFi device folder and set inherited host properties to
   **No IP**, **No API integrations, no Checkmk agent**, **No SNMP**, and
   **Always use piggyback data**. These are DEVICE-host settings; retain the
   controller host's special-agent integration. Scope its connection rule to
   the controller host so it is not inherited by the device hosts.
4. Use the folder's CSV host import action. Select semicolon as separator and
   map `hostname` to the Checkmk host name and `alias` to the alias. Treat the
   first row as column headings. The CSV deliberately leaves connection
   properties to the folder instead of depending on internal property names.
5. Test by importing two rows first, activate the new hosts and run service
   discovery. Confirm data arrives under the MAC-based hostnames.
6. Import the remaining rows, avoiding duplicates already imported. Run bulk
   service discovery on the device hosts, accept discovered services, and
   activate changes. Expect Device, Statistics and available port services.

The helper exports only sites included in the controller's rule. For multiple
controllers, export each independently and check duplicate hostnames before
import. Re-running it does not update or delete existing Checkmk hosts: review
changes and use the importer's supported update behavior or import new rows
only. Device aliases are readable names; MAC-based hostnames must stay intact.
