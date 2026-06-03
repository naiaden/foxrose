from events.event import Event
from routing.rules import ROUTING_RULES, routing_rule, DeliveryType


class NotificationRouter:
    def __init__(self, state_manager, sinks: list):
        self.state = state_manager  # Holds cache of user preferences, active mode, snoozes
        self.sinks = sinks          # List of active NotificationSink instances

    def route_event(self, event: Event):

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