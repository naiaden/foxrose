from __future__ import annotations

from events.event import Event, color_wrap
from enum import Enum, auto
from typing import Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from colorama import Fore

if TYPE_CHECKING:
    from users import User


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
    SNOOZE_SPECIFIC = auto()


@dataclass(frozen=True)
class UserSettingsChangedEvent(ChangeEvent):
    user: User
    settings_type: UserSettingsType
    settings_value: Optional[Any] = None
    value: Optional[Any] = None

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserSettingsChangedEvent: {self.user} {self.settings_type} {self.settings_value} {self.value}"


@dataclass(frozen=True)
class UserSnoozeEvent(UserSettingsChangedEvent):
    settings_type: UserSettingsType = UserSettingsType.SNOOZE
    value: int | float

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserSnoozeEvent: {self.user} (snoozed for {self.value})"


@dataclass(frozen=True)
class UserModeToggleEvent(UserSettingsChangedEvent):
    settings_type: UserSettingsType = UserSettingsType.MODE

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserModeToggleEvent: {self.user} -- Toggled: {self.value}"
