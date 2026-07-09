"""Handler for presence detection events."""

from logging_config import logger

from events import (
    PresenceDetectionEvent,
    IndoorPresenceDetectionEvent,
    OutdoorPresenceDetectionEvent,
)
from sensors import SensorType
from routing.rules import routing_rule, DeliveryType


class PresenceDetectionEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(PresenceDetectionEvent, self.handle_presence_event)

    def handle_presence_event(self, event: PresenceDetectionEvent):

        if type(event) is PresenceDetectionEvent:
            sensor = self.state.get_sensor(event.device)
            self.state.presence_detected(sensor, event._create_time)

            if sensor:
                # Check if we should route this event (outside the window)
                if not self.state.should_route_presence_event(
                    sensor.device_id, event._create_time
                ):
                    logger.debug(
                        f"Suppressing presence event for {sensor!s} (within {self.state._sensors.window_timeout}s window)"
                    )
                    return

                # Mark that we're routing this event
                self.state.mark_presence_event_routed(
                    sensor.device_id, event._create_time
                )

                if sensor.sensor_type == SensorType.INDOOR:
                    self.router.route_event(IndoorPresenceDetectionEvent(device=sensor))

                if sensor.sensor_type == SensorType.OUTDOOR:
                    self.router.route_event(
                        OutdoorPresenceDetectionEvent(device=sensor)
                    )
            else:
                logger.info(
                    f"Handled Presence Event for unknown/unregistered sensor {event.device}"
                )
            return

        user = self.state.users.get_all_users()[0]
        if (
            rule := routing_rule(self.state.get_user_mode(user), event)
        ) != DeliveryType.IGNORE:
            if user.wants_notification(event):
                for sink in self.router.sinks:
                    sink.send(
                        user,
                        f"Presence detected on {event.device!s}",
                        None,
                        rule == DeliveryType.SILENT,
                    )
