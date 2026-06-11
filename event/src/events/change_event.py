from events.event import Event, color_wrap
from enum import Enum, auto
from typing import Optional, Any
from dataclasses import dataclass
from users import User
from colorama import Fore
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ChangeEvent(Event):
    _SS = f"{Fore.CYAN}"

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] ChangeEvent"

@dataclass(frozen=True)
class SettingsChangedEvent(ChangeEvent):
    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] SettingsChangedEvent"


class UserSettingsType(Enum):
    CAMERA_PREFERENCE = auto()
    MODE = auto()
    SNOOZE = auto()

@dataclass(frozen=True)
class UserSettingsChangedEvent(ChangeEvent):
    user: User
    settings_type: UserSettingsType
    settings_value: Optional[Any] = None
    value: Optional[Any] = None

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserSettingsChangedEvent: {self.user} {self.settings_type} {self.settings_value} {self.value}"


class UserSnoozeEvent(UserSettingsChangedEvent):
    settings_type: UserSettingsType = UserSettingsType.SNOOZE
    value: int|float

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserSnoozeEvent: {self.user} (snoozed for {self.value})"



class UserModeToggleEvent(UserSettingsChangedEvent):
    settings_type: UserSettingsType = UserSettingsType.MODE

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserModeToggleEvent: {self.user} -- Toggled: {self.value}"
