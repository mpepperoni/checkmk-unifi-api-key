from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, model_validator

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
    username: str | None = None
    password: Secret | None = None
    api_key: Secret | None = None
    port: int = 443
    udm_pro: bool = False
    sites: list[str] | None = None
    device_piggyback: bool = False
    user_piggyback: UserPiggybackParams | None = None
    user_piggyback_site: bool = False
    no_cert_check: bool = False

    @model_validator(mode="after")
    def validate_authentication(self):
        if self.api_key is not None:
            if self.username or self.password is not None or self.udm_pro or self.user_piggyback is not None or self.user_piggyback_site:
                raise ValueError("API-key mode cannot use login credentials, UDM-Pro or legacy client piggyback")
        elif not self.username or self.password is None:
            raise ValueError("Supply an API key or both username and password")
        return self


def agent_unifi_arguments(
        params: UniFiParams,
        host_config: HostConfig,
) -> Iterable[SpecialAgentCommand]:
    hostname = params.hostname or host_config.name # host_config.primary_ip_config.address
    arguments: list[str | Secret] = [
        "--hostname", hostname,
        "--port", str(params.port),
    ]
    if params.api_key is not None:
        arguments.extend(["--api-key-ref", params.api_key])
    else:
        assert params.username is not None and params.password is not None
        arguments.extend(["--username", params.username, "--password-ref", params.password])
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
