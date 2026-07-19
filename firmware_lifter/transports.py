from __future__ import annotations

import re
import subprocess
import shlex
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional

from .config import (
    ConfigError,
    CustomTransportDetails,
    GdbTransportDetails,
    OpenOcdTransportDetails,
    ResolvedProfile,
    Stm32FlashTransportDetails,
    TransportConfig,
)


PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


@dataclass(frozen=True)
class ExecutionError(Exception):
    phase: str
    returncode: int
    stderr: Optional[str] = None


def _run(command, *, phase: str, **kwargs) -> None:
    try:
        subprocess.run(
            command,
            check=True,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )
    except subprocess.CalledProcessError as exc:
        raise ExecutionError(
            phase=phase,
            returncode=exc.returncode,
            stderr=exc.stderr,
        ) from None
    except FileNotFoundError:
        raise ExecutionError(phase=phase, returncode=127) from None


def execute_profile(profile: ResolvedProfile) -> None:
    if profile.pre_transfer:
        _run(
            profile.pre_transfer,
            phase="pre_transfer",
            shell=True,
            cwd=str(profile.project_root),
        )

    command = build_transport_command(profile)
    if isinstance(command, str):
        shell = _custom_shell(profile.transport)
        _run(
            command,
            phase="transfer",
            shell=True,
            executable=shell,
            cwd=str(profile.project_root),
        )
    else:
        _run(command, phase="transfer", cwd=str(profile.project_root))


def build_transport_command(profile: ResolvedProfile):
    transport = profile.transport
    if transport.type == "gdb":
        return build_gdb_command(profile.image, transport.details)
    if transport.type == "openocd":
        return build_openocd_command(profile.image, transport.details)
    if transport.type == "stm32flash":
        return build_stm32flash_command(profile.image, transport.details)
    if transport.type == "custom":
        return render_template(profile, transport.details)
    raise ConfigError(f"Unsupported transport type: {transport.type}")


def build_gdb_command(image: str, details: GdbTransportDetails) -> List[str]:
    return [
        details.gdb_binary,
        "--batch",
        image,
        "-ex",
        f"target remote {details.target}",
        "-ex",
        "load",
    ]


def build_openocd_command(image: str, details: OpenOcdTransportDetails) -> List[str]:
    command: List[str] = [details.openocd_binary]
    for config_file in details.config_files:
        command.extend(["-f", config_file])
    command.extend(["-c", f"program {shlex.quote(image)} verify reset exit"])
    return command


def build_stm32flash_command(
    image: str, details: Stm32FlashTransportDetails
) -> List[str]:
    return [
        details.stm32flash_binary,
        "-b",
        str(details.baudrate),
        "-w",
        image,
        details.device,
    ]


def render_template(profile: ResolvedProfile, details: CustomTransportDetails) -> str:
    values = _template_values(profile)

    def replace(match: re.Match) -> str:
        key = match.group(1)
        return values.get(key, match.group(0))

    return PLACEHOLDER_RE.sub(replace, details.template)


def _custom_shell(transport: TransportConfig):
    if transport.type != "custom":
        return None
    return transport.details.shell


def _template_values(profile: ResolvedProfile) -> Dict[str, str]:
    values: Dict[str, str] = {
        "image": profile.image,
        "profile": profile.name,
        "project_root": str(profile.project_root),
        "transport_type": profile.transport.type,
    }
    values.update(_flatten_details(profile.transport.details))
    return values


def _flatten_details(details: object) -> Dict[str, str]:
    if hasattr(details, "model_dump"):
        raw = details.model_dump()
    elif isinstance(details, Mapping):
        raw = dict(details)
    else:
        return {}

    flattened: Dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            flattened[key] = " ".join(str(item) for item in value)
        else:
            flattened[key] = str(value)
    return flattened
