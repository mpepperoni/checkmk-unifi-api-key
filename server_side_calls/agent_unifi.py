from collections.abc import Iterable
from pydantic import BaseModel
from cmk.server_side_calls.v1 import HostConfig, Secret, SpecialAgentCommand, SpecialAgentConfig


class UniFiParams(BaseModel):
    hostname: str | None = None
    username: str | None = None
    password: Secret | None = None
    port: int = 443
    udm_pro: bool = False
    sites: list[str] = ["all"]
    device_piggyback: bool = False
    user_piggyback: str | None = None
    user_piggyback_name: str = "ip"
    no_cert_check: bool = False


def agent_unifi_arguments(params: UniFiParams, _host_config: HostConfig) -> Iterable[SpecialAgentCommand]:
    if not params.hostname or not params.username or params.password is None:
        return
    arguments: list[str | Secret] = ["--hostname", params.hostname, "--username", params.username, "--password-ref", params.password, "--port", str(params.port)]
    if params.udm_pro:
        arguments.append("--udm-pro")
    if params.sites:
        arguments.extend(["--sites", *params.sites])
    if params.device_piggyback:
        arguments.append("--device-piggyback")
    if params.user_piggyback:
        arguments.extend(["--user-piggyback", params.user_piggyback, "--user-piggyback-name", params.user_piggyback_name])
    if params.no_cert_check:
        arguments.append("--no-cert-check")
    yield SpecialAgentCommand(command_arguments=arguments)


special_agent_unifi = SpecialAgentConfig(name="unifi", parameter_parser=UniFiParams.model_validate, commands_function=agent_unifi_arguments)
