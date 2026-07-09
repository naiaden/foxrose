import yaml
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

from users import User
from sensors import Sensor, SensorType


@dataclass
class DoorConfig:
    ip: str
    account: str
    password: str
    location: str = ""


@dataclass
class MQTTConfig:
    main_server: str
    frigate_server: str


@dataclass
class NotificationConfig:
    doorbell_topic: str
    bot_name: str


@dataclass
class Config:
    mqtt: MQTTConfig
    doors: Dict[str, DoorConfig]
    notification: NotificationConfig
    users: List[User]
    valid_doorcards: List[str]
    frigate_cameras: List[str]
    thermometers: Dict[str, str]
    sensors: List[Sensor]
    presence_window_seconds: int = 300  # Default 5 minutes


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file."""
    path = Path(config_path)

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    # Parse MQTT config
    mqtt = MQTTConfig(
        main_server=data["mqtt"]["main_server"],
        frigate_server=data["mqtt"]["frigate_server"],
    )

    # Parse door configs
    doors = {}
    for door_name, door_data in data.get("doors", {}).items():
        doors[door_name] = DoorConfig(
            ip=door_data["ip"],
            account=door_data["account"],
            password=door_data["password"],
            location=door_data.get("location", ""),
        )

    # Parse notification config
    notification = NotificationConfig(
        doorbell_topic=data["notification"]["doorbell_topic"],
        bot_name=data["notification"]["bot_name"],
    )

    # Parse users
    users = []
    for user_data in data.get("users", []):
        users.append(
            User(
                name=user_data["name"],
                telegram_user_id=user_data.get("telegram_id"),
                keycards=user_data.get("keycards", []),
            )
        )

    # Parse valid doorcards
    valid_doorcards = data.get("valid_doorcards", [])

    # Parse frigate cameras
    frigate_cameras = data.get("frigate_cameras", [])

    # Parse thermometers
    thermometers = data.get("thermometers", {})

    # Parse sensors
    sensors = []
    for sensor_data in data.get("sensors", []):
        sensors.append(
            Sensor(
                device_id=sensor_data["device_id"],
                name=sensor_data["name"],
                sensor_type=SensorType[sensor_data["type"].upper()],
            )
        )

    # Parse presence window timeout (default 300 seconds = 5 minutes)
    presence_window_seconds = data.get("presence_window_seconds", 300)

    return Config(
        mqtt=mqtt,
        doors=doors,
        notification=notification,
        users=users,
        valid_doorcards=valid_doorcards,
        frigate_cameras=frigate_cameras,
        thermometers=thermometers,
        sensors=sensors,
        presence_window_seconds=presence_window_seconds,
    )
