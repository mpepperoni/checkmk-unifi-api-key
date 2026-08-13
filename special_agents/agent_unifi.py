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
from collections.abc import Sequence
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
) -> list[dict[str, Any]]:
    lldp_neighbors_by_port: dict[Any, list[dict[str, Any]]] = {}
    for lldp_neighbor in device.get("lldp_table", []):
        if not isinstance(lldp_neighbor, dict):
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
        for device in devices:
            host = str(device.get("name") or f"{device.get('model', 'unifi')}-{str(device.get('serial', 'unknown'))[-4:]}")
            piggyback_header(host)
            write_section("unifi_device", device)
            write_section("unifi_device_if", interfaces_with_lldp_neighbors(device))
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
