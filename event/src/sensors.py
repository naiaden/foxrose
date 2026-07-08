from dataclasses import dataclass
from enum import Enum, auto

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
    def from_string(cls, string:str):
        device_id, name, sensor_type = string.split(":")
        sensor_type = SensorType[sensor_type.strip().upper()]
        return cls(device_id, name, sensor_type)

    def __str__(self):
        return f"[{self.device_id}] {self.name} ({self.sensor_type})"

class SensorSystem:
    def __init__(self, state, sensors):
        self.state = state

        self.sensors = []
        for device_id, name, sensor_type in sensors:
            self.sensors.append(Sensor(device_id=device_id, name=name, sensor_type=SensorType[sensor_type.strip().upper()]))
        
        logger.info(f"{sensors=}")

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
        self.last_updates[sensor.device_id] = max(timestamp, self.last_updates.get(sensor.device_id,0))