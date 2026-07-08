from typing import Dict, List, Any, Set
from datetime import datetime
from logging_config import logger

from enum import Enum
from users import UserManager, User
from events.event import Event
from temperatures import TemperatureTrend, TemperatureSystem

from sensors import Sensor, SensorSystem
from modes import Mode

class StateManager:
    def __init__(self, users:List[User], allowed_users: List[str], valid_doorcards:Set[str], sensors, cameras: List[str], thermometers:List[str]):
        self.users = UserManager(
            users=users,
            allowed_user_names=allowed_users,
        )
        self._valid_doorcards = valid_doorcards

        self._current_house_mode = Mode.AT_HOME
        self._cameras = cameras
        self._temperatures = TemperatureSystem(self, thermometers)

        self._sensors = SensorSystem(self, sensors)

    def presence_detected(self, sensor, timestamp):
        return self._sensors.update_presence(sensor, timestamp)

    def get_sensors(self):
        return self._sensors.get_sensors()

    def get_sensor(self, device_id):
        return self._sensors.get_sensor(device_id)

    def is_doorcard_valid(self, card_id:str):
        return card_id in self._valid_doorcards

    def user_is_allowed(self, user:User) -> bool:
        return self.users.is_allowed(user)

    def user_wants_event(self, user: User, event: Event) -> bool:
        return user.wants_notification(event)

    def set_user_mode(self, user:User, mode:Mode):
        return self.users.set_user_mode(user, mode)

    def get_user_mode(self, user:User) -> Mode:
        return self.users.get_user_mode(user)

    def user_from_telegram_id(self, user_id) -> User:
        return self.users.get_user_from_telegram_id(user_id)
    
    def user_from_doorcard(self, card_id:str):
        return self.users.get_user_from_doorcard(card_id)

    def add_temperature_reading(self, device:str, temp:float, timestamp:datetime) -> TemperatureTrend:
        return self._temperatures.add_reading(device, temp, timestamp)
