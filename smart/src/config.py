from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class HueBridgeConfig:
    ip: str
    key: str


@dataclass
class SmartConfig:
    default_active_rooms: list[str] = field(
        default_factory=lambda: ["eetkamer", "woonkamer"]
    )


_config: SmartConfig | None = None


def load_config(config_path: str = "config.yaml") -> SmartConfig:
    """Load configuration from YAML file."""
    global _config
    if _config is not None:
        return _config

    path = Path(config_path)
    if not path.exists():
        _config = SmartConfig()
        return _config

    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    _config = SmartConfig(
        default_active_rooms=data.get(
            "default_active_rooms", ["eetkamer", "woonkamer"]
        ),
    )
    return _config


def get_hue_bridges() -> list[HueBridgeConfig]:
    """Return configured Hue bridges from environment variables."""
    import os

    bridges = []
    primary = HueBridgeConfig(
        ip=os.environ.get("HUE_IP", ""),
        key=os.environ.get("HUE_KEY", ""),
    )
    if primary.ip and primary.key:
        bridges.append(primary)

    secondary = HueBridgeConfig(
        ip=os.environ.get("HUE1_IP", ""),
        key=os.environ.get("HUE1_KEY", ""),
    )
    if secondary.ip and secondary.key:
        bridges.append(secondary)

    return bridges
