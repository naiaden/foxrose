from enum import Enum

from events.detection_event import (
    CameraDetectionEvent,
    IndoorPresenceDetectionEvent,
    OutdoorPresenceDetectionEvent,
)
from events.change_event import ChangeEvent

from modes import Mode
from events.event import Event


class DeliveryType(Enum):
    IGNORE = "ignore"
    SILENT = "silent"
    LOUD = "loud"


ROUTING_RULES = {
    Mode.AT_HOME: {
        CameraDetectionEvent: DeliveryType.SILENT,
        IndoorPresenceDetectionEvent: DeliveryType.IGNORE,
        OutdoorPresenceDetectionEvent: DeliveryType.SILENT,
        ChangeEvent: DeliveryType.IGNORE,
    },
    Mode.AWAY: {
        CameraDetectionEvent: DeliveryType.LOUD,
        IndoorPresenceDetectionEvent: DeliveryType.LOUD,
        OutdoorPresenceDetectionEvent: DeliveryType.LOUD,
        ChangeEvent: DeliveryType.IGNORE,
    },
    Mode.NIGHT: {
        CameraDetectionEvent: DeliveryType.LOUD,
        IndoorPresenceDetectionEvent: DeliveryType.IGNORE,
        OutdoorPresenceDetectionEvent: DeliveryType.LOUD,
        ChangeEvent: DeliveryType.IGNORE,
    },
}


def routing_rule(mode: Mode, event: Event | type[Event]) -> DeliveryType:
    mode_rules = ROUTING_RULES.get(mode, {})

    event_class = event if isinstance(event, type) else type(event)

    for cls in event_class.__mro__:
        if cls in mode_rules:
            return mode_rules[cls]

    return DeliveryType.SILENT
