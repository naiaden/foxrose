"""Event handlers for the notification router."""

from .afval import AfvalEventHandler
from .user_settings import UserSettingChangedEventHandler
from .snooze import SnoozeEventHandler
from .mode_toggle import ModeToggleEventHandler
from .doorcard import DoorcardEventHandler
from .camera_detection import CameraDetectionEventHandler
from .device import DeviceEventHandler
from .temperature import TemperatureEventHandler
from .presence import PresenceDetectionEventHandler

__all__ = [
    "AfvalEventHandler",
    "UserSettingChangedEventHandler",
    "SnoozeEventHandler",
    "ModeToggleEventHandler",
    "DoorcardEventHandler",
    "CameraDetectionEventHandler",
    "DeviceEventHandler",
    "TemperatureEventHandler",
    "PresenceDetectionEventHandler",
]
