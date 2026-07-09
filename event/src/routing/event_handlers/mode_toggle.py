"""Handler for mode toggle events."""

from events import UserModeToggleEvent


class ModeToggleEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(UserModeToggleEvent, self.handle_user_mode_event)

    def handle_user_mode_event(self, event: UserModeToggleEvent):
        value = event.value
        if value is None:
            value = not self.state.get_user_mode(event.user)

        self.state.set_user_mode(event.user, value)
