"""Handler for user settings change events."""

from logging_config import logger

from events import UserSettingsType, UserSettingsChangedEvent


class UserSettingChangedEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(UserSettingsChangedEvent, self.handle_change_event)

    def handle_change_event(self, event: UserSettingsChangedEvent):
        logger.debug(
            f"{event.user=} {event.settings_type=} {event.settings_value=} {event.value=}"
        )
        if event.settings_type == UserSettingsType.CAMERA_PREFERENCE:
            event.user.set_camera_interest(event.settings_value, event.value)

        if event.settings_type == UserSettingsType.MODE:
            self.state.set_user_mode(event.user, event.value)
