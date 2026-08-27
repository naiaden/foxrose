from typing import Dict, List, Set
from datetime import datetime

from users import UserManager, User
from events.event import Event
from temperatures import TemperatureTrend, TemperatureSystem

from sensors import Sensor, SensorSystem
from modes import Mode


class StateManager:
    def __init__(
        self,
        users: List[User],
        valid_doorcards: Set[str],
        sensors: List[Sensor],
        cameras: List[str],
        thermometers: Dict[str, str],
        presence_window_seconds: int = 300,
    ):
        # All users in the config are allowed by default
        self.users = UserManager(
            users=users,
            allowed_user_names=[u.name for u in users],
        )
        self._valid_doorcards = valid_doorcards

        self._current_house_mode = Mode.AT_HOME
        self._cameras = cameras
        self._temperatures = TemperatureSystem(self, thermometers)

        self._sensors = SensorSystem(
            self, sensors, window_timeout=presence_window_seconds
        )

    def presence_detected(self, sensor, timestamp):
        return self._sensors.update_presence(sensor, timestamp)

    def get_sensors(self):
        return self._sensors.get_sensors()

    def get_sensor(self, device_id):
        return self._sensors.get_sensor(device_id)

    def is_doorcard_valid(self, card_id: str):
        return card_id in self._valid_doorcards

    def user_is_allowed(self, user: User) -> bool:
        return self.users.is_allowed(user)

    def user_wants_event(self, user: User, event: Event) -> bool:
        return user.wants_notification(event)

    def set_user_mode(self, user: User, mode: Mode):
        return self.users.set_user_mode(user, mode)

    def get_user_mode(self, user: User) -> Mode:
        return self.users.get_user_mode(user)

    def user_from_telegram_id(self, user_id) -> User:
        return self.users.get_user_from_telegram_id(user_id)

    def user_from_doorcard(self, card_id: str):
        return self.users.get_user_from_doorcard(card_id)

    def add_temperature_reading(
        self, device: str, temp: float, timestamp: datetime
    ) -> TemperatureTrend:
        return self._temperatures.add_reading(device, temp, timestamp)

    def should_route_presence_event(self, sensor_id: str, current_time: float) -> bool:
        """Check if a presence event should be routed (outside the window)."""
        return self._sensors.should_route_event(sensor_id, current_time)

    def mark_presence_event_routed(self, sensor_id: str, timestamp: float):
        """Record that a presence event was routed."""
        self._sensors.mark_event_routed(sensor_id, timestamp)

    def is_new_presence_window(self, sensor_id: str, current_time: float) -> bool:
        """Check if this event starts a new window (after window expiration, not first time)."""
        return self._sensors.is_new_window(sensor_id, current_time)
