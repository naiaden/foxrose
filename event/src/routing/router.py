from events.event import Event
from events.afval_event import AfvalEvent
from events.change_event import UserSettingsType, UserModeToggleEvent, UserSnoozeEvent, UserSettingsChangedEvent
from routing.rules import ROUTING_RULES, routing_rule, DeliveryType
from events.doorcard_event import DoorCardEvent
from events.detection_event import DetectionEvent, OutdoorPresenceDetectionEvent, IndoorPresenceDetectionEvent, PresenceDetectionEvent
from events.device_event import DeviceEvent, BatteryEvent, LowBatteryEvent, TemperatureEvent
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

from modes import Mode

class AfvalEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(AfvalEvent, self.handle_afval_event)

    def handle_afval_event(self, event: AfvalEvent):
        for sink in self.router.sinks:
            sink.send(None, event.message, None, True)

class UserSettingChangedEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(UserSettingsChangedEvent, self.handle_change_event)

    def handle_change_event(self, event: UserSettingsChangedEvent):
        if event.settings_type == UserSettingsType.CAMERA_PREFERENCE:
            event.user.set_camera_interest(event.settings_value, event.value)

        if event.settings_type == UserSettingsType.MODE:
            event.user.set_camera_interest(event.settings_value, event.value)

class SnoozeEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(UserSnoozeEvent, self.handle_snooze_event)

    def handle_snooze_event(self, event: UserSnoozeEvent):
        if event.value is None:
            event.user.reset_snooze()
            return

        if isinstance(event.value, str):
            amount, unit = event.value.split(' ')
            duration = amount
            
            unit = unit.rstrip('s')

            if unit.endswith('Min'):
                duration *= 60
            elif unit.endswith("Hour"):
                duration *= 60 * 60
            elif unit.endswith("Day"):
                duration *= 24 * 60 * 60

            event.user.snooze_for(duration)
            return

        if isinstance(self.value, (int, float)):
            event.user.snooze_for(self.value)
            return

class ModeToggleEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(UserModeToggleEvent, self.handle_user_mode_event)

    def handle_user_mode_event(self, event: UserModeToggleEvent):
        value = event.value
        if value is None:
            value = not self.state.get_user_mode(event.user)

        event.user.mode = value

class DoorcardEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(DoorCardEvent, self.handle_doorcard)

    def handle_doorcard(self, event: DoorCardEvent):
        user = self.state.user_from_doorcard(event.card_number)
        self.route_event(UserModeToggleEvent(user))

class DetectionEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(DetectionEvent, self.handle_detection_event)

    def handle_detection_event(self, event: DetectionEvent):
        for user in self.state.users.get_all_users():

            user_mode = self.state.get_user_mode(user)
            priority = routing_rule(user_mode, event)

            if priority == DeliveryType.IGNORE:
                return

            is_silent = (priority == DeliveryType.SILENT)

            if self.state.user_wants_event(user, event):
                for sink in self.sinks:
                    sink.send(
                        user=user,
                        message=f"Movement on {getattr(event, 'camera_name', 'sensor')}",
                        payload=getattr(event, 'payload', {}),
                        silent=is_silent
                    )

class DeviceEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(DeviceEvent, self.handle_device_event)

    def handle_device_event(self, event:DeviceEvent):
        if isinstance(event, BatteryEvent):
            if event.percentage < 10:
                self.router.route_event(LowBatteryEvent(event.device, event.percentage))

class TemperatureEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(TemperatureEvent, self.handle_temperature_event)

    def handle_temperature_event(self, event:TemperatureEvent):
        if isinstance(event, TemperatureEvent):
            self.state.add_temperature_reading(event.device, event.temperature, event._create_time)

class PresenceDetectionEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(PresenceDetectionEvent, self.handle_presence_event)

    def handle_presence_event(self, event:PresenceDetectionEvent):
        if isinstance(event, PresenceDetectionEvent):
            # if True: # indoor PIR
            #     self.router.route_event(IndoorPresenceDetectionEvent(event.device))
            # else:
            #     self.router.route_event(OutdoorPresenceDetectionEvent(event.device))

            return

        if isinstance(event, IndoorPresenceDetectionEvent):
            return

        if isinstance(event, OutdoorPresenceDetectionEvent):
            return




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
        logger.info(f"Routing {event!s}")

        for cls in event.__class__.__mro__:
            if cls in self._subscribers:
                for callback in self._subscribers[cls]:
                    callback(event)
                break # don't bubble up

        
