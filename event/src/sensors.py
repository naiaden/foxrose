from dataclasses import dataclass
from enum import Enum, auto
from typing import List

from logging_config import logger


class SensorType(Enum):
    INDOOR = auto()
    OUTDOOR = auto()
    UNKNOWN = auto()


@dataclass
class Sensor:
    device_id: str
    name: str
    sensor_type: SensorType

    @classmethod
    def from_string(cls, string: str):
        device_id, name, sensor_type = string.split(":")
        sensor_type = SensorType[sensor_type.strip().upper()]
        return cls(device_id, name, sensor_type)

    def __str__(self):
        return f"[{self.device_id}] {self.name} ({self.sensor_type})"


class SensorSystem:
    def __init__(self, state, sensors: List[Sensor] = None):
        self.state = state

        self.sensors = sensors or []

        logger.info(f"Initialized {len(self.sensors)} sensors")

        self.last_updates = {}

    # def get_sensors(self):

    def get_sensor(self, sensor_id):
        for sensor in self.sensors:
            if sensor.device_id == sensor_id:
                return sensor

        new_sensor = Sensor(sensor_id, sensor_id, SensorType.UNKNOWN)
        self.sensors.append(new_sensor)
        return new_sensor

    def update_presence(self, sensor, timestamp):
        logger.info(f"updating presence on {sensor!s}")
        self.last_updates[sensor.device_id] = max(
            timestamp, self.last_updates.get(sensor.device_id, 0)
        )
