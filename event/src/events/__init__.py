"""Event classes for the FoxRose system."""

from events.afval_event import AfvalEvent
from events.change_event import (
    ChangeEvent,
    SettingsChangedEvent,
    UserSettingsChangedEvent,
    UserSettingsType,
    UserSnoozeEvent,
    UserModeToggleEvent,
)
from events.detection_event import (
    DetectionEvent,
    DetectionConfidence,
    CameraLoiteringEvent,
    CameraDetectionEvent,
    PresenceDetectionEvent,
    IndoorPresenceDetectionEvent,
    OutdoorPresenceDetectionEvent,
    PresenceWindowStartedEvent,
)
from events.doorcard_event import DoorCardEvent
from events.device_event import (
    DeviceEvent,
    BatteryEvent,
    LowBatteryEvent,
    TemperatureEvent,
)

__all__ = [
    "AfvalEvent",
    "ChangeEvent",
    "SettingsChangedEvent",
    "UserSettingsChangedEvent",
    "UserSettingsType",
    "UserSnoozeEvent",
    "UserModeToggleEvent",
    "DetectionEvent",
    "DetectionConfidence",
    "CameraLoiteringEvent",
    "CameraDetectionEvent",
    "PresenceDetectionEvent",
    "IndoorPresenceDetectionEvent",
    "OutdoorPresenceDetectionEvent",
    "PresenceWindowStartedEvent",
    "DoorCardEvent",
    "DeviceEvent",
    "BatteryEvent",
    "LowBatteryEvent",
    "TemperatureEvent",
]
