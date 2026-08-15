#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# (c) 2026 Frank Baier
# @author Frank Baier <dev@baier-nt.de>
#
from __future__ import annotations
import argparse
import pathlib
import sys
from collections.abc import Mapping, Sequence
from typing import Any
import requests
import urllib3
from cmk.special_agents.v0_unstable.agent_common import SectionWriter, special_agent_main
from cmk.special_agents.v0_unstable.argument_parsing import Args, create_default_argument_parser
from cmk.utils import password_store

REQUEST_TIMEOUT_SECONDS = 20


def main() -> int:
    return special_agent_main(parse_arguments, run_agent)


def parse_arguments(
        argv: Sequence[str],
) -> argparse.Namespace:
    parser = create_default_argument_parser(description=__doc__)
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--username", required=True)
    password_group = parser.add_mutually_exclusive_group(required=True)
    password_group.add_argument("--password-ref")
    password_group.add_argument("--password")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--udm-pro", action="store_true")
    parser.add_argument("--sites", nargs="*", default=["all"])
    parser.add_argument("--device-piggyback", action="store_true")
    parser.add_argument("--user-piggyback", choices=("ip", "hostname", "hostname_domain"))
    parser.add_argument("--user-piggyback-domain")
    parser.add_argument("--user-piggyback-site", action="store_true")
    parser.add_argument("--no-cert-check", action="store_true")
    args = parser.parse_args(argv)
    if args.user_piggyback == "hostname_domain" and not args.user_piggyback_domain:
        parser.error("--user-piggyback-domain is required for hostname_domain piggyback names")
    return args


def password(
        args: argparse.Namespace,
) -> str:
    if args.password:
        return args.password
    password_id, password_file = args.password_ref.split(":", maxsplit=1)
    return password_store.lookup(pathlib.Path(password_file), password_id)


def write_section(
        name: str,
        data: Any,
) -> None:
    with SectionWriter(name) as writer:
        writer.append_json(data)


def request(
        session: requests.Session,
        url: str,
        verify: bool,
) -> Any:
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS, verify=verify)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"UniFi API request failed for {url}: {exc}") from exc
    if not isinstance(payload, dict) or "data" not in payload:
        raise RuntimeError(f"UniFi API response for {url} does not contain data")
    return payload["data"]


def piggyback_header(
        hostname: str,
) -> None:
    print(f"<<<<{hostname}>>>>")


def user_piggyback_hostname(
        user: dict[str, Any],
        args: argparse.Namespace,
) -> str | None:
    if args.user_piggyback == "ip":
        return user.get("ip")

    hostname = user.get("hostname")
    if not hostname:
        return None
    if args.user_piggyback == "hostname":
        return hostname

    domain = args.user_piggyback_domain.strip(".")
    hostname = hostname.rstrip(".")
    if hostname.lower() == domain.lower() or hostname.lower().endswith(f".{domain.lower()}"):
        return hostname
    return f"{hostname}.{domain}"


def interfaces_with_lldp_neighbors(
        device: dict[str, Any],
        wired_clients_by_switch_port: Mapping[tuple[str, int], set[str]],
) -> list[dict[str, Any]]:
    lldp_neighbors_by_port: dict[Any, list[dict[str, Any]]] = {}
    for lldp_neighbor in device.get("lldp_table", []):
        if not isinstance(lldp_neighbor, dict) or is_wired_client_lldp_entry(
            device, lldp_neighbor, wired_clients_by_switch_port
        ):
            continue
        local_port_idx = lldp_neighbor.get("local_port_idx")
        if local_port_idx is None:
            continue
        lldp_neighbors_by_port.setdefault(local_port_idx, []).append(lldp_neighbor)
    interfaces = []
    for port in device.get("port_table", []):
        if not isinstance(port, dict):
            continue
        interface = port.copy()
        if lldp_neighbors := lldp_neighbors_by_port.get(interface.get("port_idx")):
            interface["lldp_neighbors"] = lldp_neighbors
        interfaces.append(interface)
    return interfaces


def wired_clients_by_switch_port(
        users: list[dict[str, Any]],
) -> dict[tuple[str, int], set[str]]:
    """Index wired UniFi clients by the switch port that serves them.

    Recent UniFi controller versions can add a wired client's MAC address to a
    switch's ``lldp_table``.  A client is not an LLDP neighbor; its presence
    can be identified reliably through its matching ``sw_mac`` and
    ``sw_port`` in the controller's client data.
    """
    clients: dict[tuple[str, int], set[str]] = {}
    for user in users:
        if not (
            isinstance(user, dict)
            and user.get("is_wired") is True
            and isinstance(switch_mac := user.get("sw_mac"), str)
            and isinstance(switch_port := user.get("sw_port"), int)
            and isinstance(client_mac := user.get("mac"), str)
        ):
            continue
        clients.setdefault((switch_mac.lower(), switch_port), set()).add(
            client_mac.lower()
        )
    return clients


def is_wired_client_lldp_entry(
        device: dict[str, Any],
        neighbor: dict[str, Any],
        wired_clients: Mapping[tuple[str, int], set[str]],
) -> bool:
    """Return whether a purported LLDP entry is a UniFi wired client."""
    device_mac = device.get("mac")
    local_port = neighbor.get("local_port_idx")
    chassis_id = neighbor.get("chassis_id")
    return (
        isinstance(device_mac, str)
        and isinstance(local_port, int)
        and isinstance(chassis_id, str)
        and chassis_id.lower()
        in wired_clients.get((device_mac.lower(), local_port), set())
    )


def lldp_lag_remote_port_idx(
        device: dict[str, Any],
        neighbor: dict[str, Any],
        remote_device: dict[str, Any] | None,
) -> int | None:
    """Resolve an LLDP port within a LAG from its reciprocal LLDP entries.

    UniFi's ``uplink_remote_port`` describes only one member of an aggregate.
    Consequently it maps every member of a LAG to that first port.  Both ends
    do however report one LLDP entry per physical link.  When the local port
    belongs to a LAG, pair the sorted local members with the sorted reciprocal
    remote ports.  This makes the mapping deterministic while retaining the
    existing uplink-based fallback for ordinary links.
    """
    local_port_idx = neighbor.get("local_port_idx")
    remote_mac = neighbor.get("chassis_id")
    device_mac = device.get("mac")
    if not (
        remote_device
        and isinstance(local_port_idx, int)
        and isinstance(remote_mac, str)
        and isinstance(device_mac, str)
    ):
        return None

    lag_members = next(
        (
            group.get("aggregate_members")
            for group in device.get("link_aggregation_groups", [])
            if isinstance(group, dict)
            and isinstance(group.get("aggregate_members"), list)
            and local_port_idx in group["aggregate_members"]
        ),
        None,
    )
    if not lag_members:
        return None

    local_members = sorted(
        entry["local_port_idx"]
        for entry in device.get("lldp_table", [])
        if isinstance(entry, dict)
        and entry.get("local_port_idx") in lag_members
        and isinstance(entry.get("local_port_idx"), int)
        and isinstance(entry.get("chassis_id"), str)
        and entry["chassis_id"].lower() == remote_mac.lower()
    )
    remote_member_groups = [
        sorted(
            entry["local_port_idx"]
            for entry in remote_device.get("lldp_table", [])
            if isinstance(entry, dict)
            and entry.get("local_port_idx") in members
            and isinstance(entry.get("local_port_idx"), int)
            and isinstance(entry.get("chassis_id"), str)
            and entry["chassis_id"].lower() == device_mac.lower()
        )
        for group in remote_device.get("link_aggregation_groups", [])
        if isinstance(group, dict)
        and isinstance(members := group.get("aggregate_members"), list)
    ]
    matching_remote_groups = [
        members for members in remote_member_groups if len(members) == len(local_members)
    ]
    if len(local_members) < 2 or len(matching_remote_groups) != 1:
        return None

    remote_members = matching_remote_groups[0]
    return remote_members[local_members.index(local_port_idx)]


def lldp_neighbors(
        device: dict[str, Any],
        devices_by_mac: dict[str, dict[str, Any]],
        wired_clients: Mapping[tuple[str, int], set[str]],
) -> list[dict[str, Any]]:
    """Return a compact LLDP section, enriched for managed UniFi neighbors."""
    neighbors = []
    for neighbor in device.get("lldp_table", []):
        if not isinstance(neighbor, dict) or is_wired_client_lldp_entry(
            device, neighbor, wired_clients
        ):
            continue

        chassis_id = neighbor.get("chassis_id")
        remote_device = (
            devices_by_mac.get(chassis_id.lower())
            if isinstance(chassis_id, str)
            else None
        )
        lldp_neighbor = {
            key: neighbor[key]
            for key in (
                "chassis_id",
                "chassis_id_subtype",
                "is_wired",
                "local_port_idx",
                "local_port_name",
                "port_id",
                "power_allocated",
                "power_requested",
            )
            if key in neighbor
        }
        uplink = device.get("uplink", {})
        remote_uplink = remote_device.get("uplink", {}) if remote_device else {}
        chassis_mac = chassis_id.lower() if isinstance(chassis_id, str) else None
        uplink_mac = uplink.get("uplink_mac")
        remote_uplink_mac = remote_uplink.get("uplink_mac")
        device_mac = device.get("mac")
        lldp_neighbor["port_idx"] = lldp_lag_remote_port_idx(
            device, neighbor, remote_device
        )
        if lldp_neighbor["port_idx"] is None:
            lldp_neighbor["port_idx"] = (
                uplink.get("uplink_remote_port")
                if isinstance(uplink_mac, str) and uplink_mac.lower() == chassis_mac
                else remote_uplink.get("port_idx")
                if isinstance(remote_uplink_mac, str)
                and isinstance(device_mac, str)
                and remote_uplink_mac.lower() == device_mac.lower()
                else None
            )
        if remote_device:
            remote_port = next(
                (
                    port
                    for port in remote_device.get("port_table", [])
                    if lldp_neighbor["port_idx"] is not None
                    and isinstance(port, dict)
                    and port.get("port_idx") == lldp_neighbor["port_idx"]
                ),
                None,
            )
            if remote_port and isinstance(remote_port.get("name"), str):
                lldp_neighbor["remote_port_name"] = remote_port["name"]
            lldp_neighbor.update(
                {
                    f"remote_{key}": remote_device[key]
                    for key in ("name", "model", "ip", "type")
                    if remote_device.get(key) is not None
                }
            )
        neighbors.append(lldp_neighbor)
    return neighbors


def devices_by_mac(
        devices: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Index UniFi devices by MAC for LLDP neighbor enrichment."""
    return {
        mac.lower(): device
        for device in devices
        if isinstance(device, dict) and isinstance(mac := device.get("mac"), str)
    }


def fetch_site(
        session: requests.Session,
        api_url: str,
        site: dict[str, Any],
        args: argparse.Namespace,
        verify: bool,
) -> None:
    site_id = site.get("name")
    site_name = str(site.get("desc") or site_id)
    if not site_id:
        return
    devices = request(session, f"{api_url}/s/{site_id}/stat/device", verify)
    users = request(session, f"{api_url}/s/{site_id}/stat/sta", verify)
    health = request(session, f"{api_url}/s/{site_id}/stat/health", verify)
    controller = request(session, f"{api_url}/s/{site_id}/stat/sysinfo", verify)
    piggyback_header(site_name)
    write_section("unifi_controller", controller[0] if isinstance(controller, list) and controller else {})
    write_section("unifi_site_controller_health", health)
    if args.user_piggyback_site:
        write_section("unifi_site_users", users)
    print("<<<<>>>>")
    if args.device_piggyback:
        site_devices_by_mac = devices_by_mac(devices)
        site_wired_clients_by_switch_port = wired_clients_by_switch_port(users)
        for device in devices:
            host = str(device.get("name") or f"{device.get('model', 'unifi')}-{str(device.get('serial', 'unknown'))[-4:]}")
            piggyback_header(host)
            write_section("unifi_device", device)
            write_section(
                "unifi_device_if",
                interfaces_with_lldp_neighbors(device, site_wired_clients_by_switch_port),
            )
            write_section(
                "unifi_device_lldp",
                lldp_neighbors(
                    device, site_devices_by_mac, site_wired_clients_by_switch_port
                ),
            )
            device_users = [user for user in users if device.get("mac") in {user.get("sw_mac"), user.get("ap_mac")}]
            write_section("unifi_device_users", device_users)
            print("<<<<>>>>")
    if args.user_piggyback is not None:
        for user in users:
            host = user_piggyback_hostname(user, args)
            if host is None:
                continue
            piggyback_header(host)
            write_section("unifi_user", user)
            print("<<<<>>>>")


def run_agent(
        args: Args,
) -> int:
    parsed_args = args
    verify = not parsed_args.no_cert_check
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    base_url = f"https://{parsed_args.hostname}:{parsed_args.port}"
    login_url = f"{base_url}/api/auth/login" if parsed_args.udm_pro else f"{base_url}/api/login"
    api_url = f"{base_url}/proxy/network/api" if parsed_args.udm_pro else f"{base_url}/api"
    session = requests.Session()
    try:
        response = session.post(
            login_url,
            json={"username": parsed_args.username, "password": password(parsed_args)},
            timeout=REQUEST_TIMEOUT_SECONDS,
            verify=verify,
        )
        response.raise_for_status()
        controller = request(session, f"{api_url}/s/default/stat/sysinfo", verify)
        sites = request(session, f"{api_url}/stat/sites", verify)
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except requests.RequestException as exc:
        sys.stderr.write(f"UniFi authentication failed: {exc}\n")
        return 1
    write_section("unifi_controller", controller[0] if isinstance(controller, list) and controller else {})
    write_section("unifi_controller_sites", sites)
    wanted_sites = set(parsed_args.sites)
    for site in sites:
        if "all" in wanted_sites or site.get("desc") in wanted_sites:
            try:
                fetch_site(session, api_url, site, parsed_args, verify)
            except RuntimeError as exc:
                sys.stderr.write(f"{exc}\n")
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
