from enum import Enum

from events.detection_event import CameraDetectionEvent, IndoorPresenceDetectionEvent, OutdoorPresenceDetectionEvent

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
    },
    Mode.AWAY: {
        CameraDetectionEvent: DeliveryType.LOUD,
        IndoorPresenceDetectionEvent: DeliveryType.LOUD,
        OutdoorPresenceDetectionEvent: DeliveryType.LOUD,
    },
    Mode.NIGHT: {
        CameraDetectionEvent: DeliveryType.LOUD,
        IndoorPresenceDetectionEvent: DeliveryType.IGNORE,
        OutdoorPresenceDetectionEvent: DeliveryType.LOUD,
    }
}

def routing_rule(mode:Mode, event_type:type[Event]) -> DeliveryType:
    if priority := ROUTING_RULES.get(mode, {}).get(event_type, None):
        return priority

    return DeliveryType.SILENT