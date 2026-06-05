from events.event import Event
from events.change_event import UserModeToggleEvent
from routing.rules import ROUTING_RULES, routing_rule, DeliveryType
from events.doorcard_event import DoorCardEvent
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class NotificationRouter:
    def __init__(self, state_manager, sinks: list):
        self.state = state_manager  # Holds cache of user preferences, active mode, snoozes
        self.sinks = sinks          # List of active NotificationSink instances

    def _process_doorcard(self, event: DoorCardEvent):
        user = self.state.user_from_doorcard(event.card_number)
        self.route_event(UserModeToggleEvent(user))

    def route_event(self, event: Event):
        logger.info(f"Routing {event!s}")

        if isinstance(event, DoorCardEvent):
            self._process_doorcard(event)
            return

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
