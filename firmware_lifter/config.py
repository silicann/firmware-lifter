from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional, Union

from ruamel.yaml import YAML
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


CONFIG_PROFILES_FILE = ".firmware-lifter-profiles.yaml"
CONFIG_TRANSPORT_FILE = ".firmware-lifter-transport.yaml"


class ConfigError(ValueError):
    pass


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ProfileConfig(StrictModel):
    image: str
    pre_transfer: Optional[str] = None


class ProjectConfig(StrictModel):
    profiles: Dict[str, ProfileConfig]


class GdbTransportDetails(StrictModel):
    gdb_binary: str
    target: str


class OpenOcdTransportDetails(StrictModel):
    openocd_binary: str
    config_files: List[str]


class Stm32FlashTransportDetails(StrictModel):
    stm32flash_binary: str
    device: str
    baudrate: int


class CustomTransportDetails(StrictModel):
    template: str
    shell: str = "/bin/sh"


class GdbTransportConfig(StrictModel):
    type: Literal["gdb"] = "gdb"
    details: GdbTransportDetails


class OpenOcdTransportConfig(StrictModel):
    type: Literal["openocd"] = "openocd"
    details: OpenOcdTransportDetails


class Stm32FlashTransportConfig(StrictModel):
    type: Literal["stm32flash"] = "stm32flash"
    details: Stm32FlashTransportDetails


class CustomTransportConfig(StrictModel):
    type: Literal["custom"] = "custom"
    details: CustomTransportDetails


TransportConfig = Union[
    GdbTransportConfig,
    OpenOcdTransportConfig,
    Stm32FlashTransportConfig,
    CustomTransportConfig,
]


class TransportFileConfig(StrictModel):
    transport: TransportConfig = Field(discriminator="type")


class ResolvedProfile(StrictModel):
    name: str
    image: str
    pre_transfer: Optional[str]
    transport: TransportConfig = Field(discriminator="type")
    project_root: Path


def load_yaml_file(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")

    yaml = YAML(typ="safe")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.load(handle) or {}

    if not isinstance(data, Mapping):
        raise ConfigError(f"YAML file must contain a mapping: {path}")

    return data


def _validate_model(adapter: TypeAdapter, data: Mapping[str, Any], label: str):
    try:
        return adapter.validate_python(data)
    except ValidationError as exc:
        raise ConfigError(f"Invalid {label}: {exc}") from exc


def load_project_config(root: Path) -> ProjectConfig:
    data = load_yaml_file(root / CONFIG_PROFILES_FILE)
    project = _validate_model(TypeAdapter(ProjectConfig), data, "project config")
    if not project.profiles:
        raise ConfigError("Project config must define at least one profile")
    return project


def load_transport_config(root: Path) -> TransportConfig:
    data = load_yaml_file(root / CONFIG_TRANSPORT_FILE)
    transport_file = _validate_model(
        TypeAdapter(TransportFileConfig), data, "transport config"
    )
    return transport_file.transport


def resolve_profile(root: Path, profile_name: str) -> ResolvedProfile:
    project = load_project_config(root)
    transport = load_transport_config(root)

    profile = project.profiles.get(profile_name)
    if profile is None:
        raise ConfigError(f"Unknown profile: {profile_name}")

    return ResolvedProfile(
        name=profile_name,
        image=profile.image,
        pre_transfer=profile.pre_transfer,
        transport=transport,
        project_root=root,
    )
