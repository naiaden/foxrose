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
    def __init__(self, state, sensors: List[Sensor] = None, window_timeout: int = 300):
        self.state = state

        self.sensors = sensors or []

        logger.info(f"Initialized {len(self.sensors)} sensors")

        self.last_updates = {}
        self.last_routed_events = {}
        self.window_timeout = window_timeout  # in seconds, default 5 minutes

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

    def should_route_event(self, sensor_id: str, current_time: float) -> bool:
        """Check if enough time has passed since the last routed event.

        Returns True if the event should be routed (new window), False if suppressed.
        """
        last_routed = self.last_routed_events.get(sensor_id, 0)
        # If no event has been routed yet, allow this one
        if last_routed == 0:
            return True
        return (current_time - last_routed) >= self.window_timeout

    def is_new_window(self, sensor_id: str, current_time: float) -> bool:
        """Check if this event starts a new window (after window expiration, not first time).

        Returns True if a previous window has expired and this is the start of a new one.
        """
        last_routed = self.last_routed_events.get(sensor_id, 0)
        # If no event has been routed yet, this is not a "new window" (it's the first)
        if last_routed == 0:
            return False
        return (current_time - last_routed) >= self.window_timeout

    def mark_event_routed(self, sensor_id: str, timestamp: float):
        """Record that an event was routed for this sensor."""
        self.last_routed_events[sensor_id] = timestamp
