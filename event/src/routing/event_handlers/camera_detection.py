"""Handler for camera detection events."""

from events import CameraDetectionEvent
from routing.rules import routing_rule, DeliveryType


class CameraDetectionEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(CameraDetectionEvent, self.handle_detection_event)

    def handle_detection_event(self, event: CameraDetectionEvent):
        for user in [self.state.users.get_all_users()[0]]:

            user_mode = self.state.get_user_mode(user)
            priority = routing_rule(user_mode, event)

            if priority == DeliveryType.IGNORE:
                continue

            is_silent = priority == DeliveryType.SILENT

            if self.state.user_wants_event(user, event):
                for sink in self.router.sinks:
                    sink.send(
                        user=user,
                        message=f"Movement on {event.camera_name}",
                        payload=event.payload,
                        silent=is_silent,
                    )
