from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel

from cmk.server_side_calls.v1 import HostConfig, Secret, SpecialAgentCommand, SpecialAgentConfig


class UserPiggybackHostnameDomainParams(BaseModel):
    domain: str


class UserPiggybackParams(BaseModel):
    user_piggyback_name: (
        tuple[Literal["ip", "hostname"], None]
        | tuple[Literal["hostname_domain"], UserPiggybackHostnameDomainParams]
    ) = ("ip", None)


class UniFiParams(BaseModel):
    hostname: str | None = None
    username: str
    password: Secret
    port: int = 443
    udm_pro: bool = False
    sites: list[str] | None = None
    device_piggyback: bool = False
    user_piggyback: UserPiggybackParams | None = None
    user_piggyback_site: bool = False
    no_cert_check: bool = False


def agent_unifi_arguments(
        params: UniFiParams,
        host_config: HostConfig,
) -> Iterable[SpecialAgentCommand]:
    hostname = params.hostname or host_config.primary_ip_config.address
    arguments: list[str | Secret] = [
        "--hostname", hostname,
        "--username", params.username,
        "--password-ref", params.password,
        "--port", str(params.port),
    ]
    if params.udm_pro:
        arguments.append("--udm-pro")
    if params.sites is not None:
        arguments.extend(["--sites", *params.sites])
    if params.device_piggyback:
        arguments.append("--device-piggyback")
    if params.user_piggyback is not None:
        user_piggyback_name, details = params.user_piggyback.user_piggyback_name
        arguments.extend([
            "--user-piggyback", user_piggyback_name,
        ])
        if user_piggyback_name == "hostname_domain":
            arguments.extend(["--user-piggyback-domain", details.domain])
    if params.user_piggyback_site:
        arguments.append("--user-piggyback-site")
    if params.no_cert_check:
        arguments.append("--no-cert-check")
    yield SpecialAgentCommand(command_arguments=arguments)


special_agent_unifi = SpecialAgentConfig(
    name="unifi",
    parameter_parser=UniFiParams.model_validate,
    commands_function=agent_unifi_arguments,
)
