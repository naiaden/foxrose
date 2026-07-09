"""Handler for doorcard events."""

from events import DoorCardEvent, UserModeToggleEvent, UserSettingsType


class DoorcardEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(DoorCardEvent, self.handle_doorcard)

    def handle_doorcard(self, event: DoorCardEvent):
        user = self.state.user_from_doorcard(event.card_number)
        self.router.route_event(
            UserModeToggleEvent(user, settings_type=UserSettingsType.MODE)
        )
