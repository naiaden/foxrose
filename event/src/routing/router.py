"""Notification router and event routing."""

from events.event import Event
from events.device_event import BatteryEvent, TemperatureEvent
from logging_config import logger


class NotificationRouter:
    def __init__(self, state_manager, sinks: list):
        self.state = state_manager
        self.sinks = sinks
        self._subscribers = {}

    def subscribe(self, event_type: type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def route_event(self, event: Event):
        if isinstance(event, (BatteryEvent, TemperatureEvent)):
            logger.debug(f"Routing {event!s}")
        else:
            logger.info(f"Routing {event!s}")

        for cls in event.__class__.__mro__:
            if cls in self._subscribers:
                for callback in self._subscribers[cls]:
                    callback(event)
                break  # don't bubble up
