from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from modes import Mode
from events.event import Event
from events.detection_event import (
    CameraDetectionEvent,
    PresenceDetectionEvent,
    IndoorPresenceDetectionEvent,
    OutdoorPresenceDetectionEvent,
)

from logging_config import logger


class User:
    def __init__(
        self, name: str, telegram_user_id: int = None, keycards: List[str] = None
    ):

        self.name = name
        self.telegram_user_id = telegram_user_id

        self._camera_preferences: Dict[str, bool] = {}

        self._keycards: Set[str] = keycards or set()

        self._snooze_time: datetime = None
        self._snoozed_event_types: Set[str] = set()
        self._mode = Mode.AT_HOME

        # Snooze tracking for state display
        self._snooze_count: int = 0
        self._last_snooze_time: datetime = None

    def __str__(self) -> str:
        return "[" + self.name + "]"

    def wants_notification(self, event: Event) -> bool:
        # Check for specific snoozed event types
        if isinstance(event, IndoorPresenceDetectionEvent):
            if "indoor_presence" in self._snoozed_event_types:
                return False
        elif isinstance(event, OutdoorPresenceDetectionEvent):
            if "outdoor_presence" in self._snoozed_event_types:
                return False
        elif isinstance(event, CameraDetectionEvent):
            if "camera" in self._snoozed_event_types:
                return False

        # Check for general snooze
        if self.is_snoozing:
            return False

        if isinstance(event, PresenceDetectionEvent):
            return self.mode != Mode.AT_HOME

        if isinstance(event, CameraDetectionEvent):
            return self.has_camera_interest(event.camera_name)

        return True

    def is_event_type_snoozed(self, event_type: str) -> bool:
        """Check if a specific event type is snoozed."""
        return event_type in self._snoozed_event_types

    def set_event_type_snoozed(self, event_type: str, value: bool = True) -> None:
        """Set or unset snooze for a specific event type."""
        if value:
            self._snoozed_event_types.add(event_type)
        else:
            self._snoozed_event_types.discard(event_type)

    def reset_all_snoozes(self) -> None:
        """Reset both general and specific snoozes."""
        self._snooze_time = None
        self._snoozed_event_types = set()

    @property
    def mode(self) -> Mode:
        return self._mode

    @mode.setter
    def mode(self, mode: Mode) -> None:
        self._mode = mode

    @property
    def is_snoozing(self) -> bool:
        if not self._snooze_time:
            return False

        return datetime.now() < self._snooze_time

    def reset_snooze(self) -> None:
        self._snooze_time = None

    def snooze_until(self, new_time: datetime) -> None:
        if not isinstance(new_time, datetime):
            raise TypeError("snooze_time must be a datetime object")
        self._snooze_time = new_time

    def snooze_for(self, duration: int | float) -> None:
        self.snooze_until(datetime.now() + timedelta(seconds=duration))
        self._snooze_count += 1
        self._last_snooze_time = datetime.now()

    def reset_snooze_count(self) -> None:
        """Reset the snooze counter (called after state is displayed)."""
        self._snooze_count = 0

    def has_camera_interest(self, camera_name: str) -> bool:
        return self._camera_preferences.get(camera_name, False)

    def set_camera_interest(self, camera_name: str, value: bool = True) -> bool:
        self._camera_preferences[camera_name] = value
        return value

    @property
    def camera_interests(self):
        return self._camera_preferences

    def uses_keycard(self, keycard_id: str) -> bool:
        return keycard_id in self._keycards

    def add_keycard(self, keycard_id: str) -> None:
        self._keycards.add(keycard_id)

    @property
    def keycards(self) -> Set[str]:
        return self._keycards


class UserManager:
    def __init__(self, users: List[User], allowed_user_names: List[str]):
        self._users = {user.name: user for user in users}
        self._allowed_users = {
            self.get_user(user_name) for user_name in allowed_user_names
        }

        logger.info(f"{len(self._users)} users initialised")
        logger.info(f"Users: {self._users.keys()}")

    def is_allowed(self, user: User) -> bool:
        return user in self._allowed_users

    def get_user(self, user_name: str) -> Optional[User]:
        return self._users.get(user_name)

    def set_user_mode(self, user: User, mode: Mode):
        for _user in self._users.values():
            if _user == user:
                user.mode = mode

    def get_user_mode(self, user: User) -> Mode:
        for _user in self._users.values():
            if _user == user:
                return _user.mode

    def get_user_from_telegram_id(self, telegram_user_id: int) -> User:

        for user in self._users.values():
            if user.telegram_user_id and user.telegram_user_id == telegram_user_id:
                return user

    def get_all_users(self) -> List[User]:
        return list(self._users.values())

    def get_user_from_doorcard(self, card_id: str) -> Optional[User]:
        for user in self._users.values():
            if user.uses_keycard(card_id):
                return user

    @staticmethod
    def from_env_string(users_as_env: str) -> List[User]:
        users = []
        for user_attributes in users_as_env.split(";"):
            user, *attributes = user_attributes.split(":")

            telegram_attr = next(
                (attribute for attribute in attributes if attribute.startswith("T")),
                None,
            )
            telegram_id = int(telegram_attr.lstrip("T")) if telegram_attr else None

            keycard_attr = next(
                (attribute for attribute in attributes if attribute.startswith("K")),
                None,
            )
            keycards = keycard_attr.lstrip("K").split(",") if keycard_attr else []

            users.append(User(user, telegram_id, keycards))

        return users
