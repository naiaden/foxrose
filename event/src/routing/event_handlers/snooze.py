"""Handler for snooze events."""

from events import UserSnoozeEvent, UserSettingsChangedEvent, UserSettingsType


class SnoozeEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(UserSnoozeEvent, self.handle_snooze_event)
        self.router.subscribe(
            UserSettingsChangedEvent, self.handle_specific_snooze_event
        )

    def handle_snooze_event(self, event: UserSnoozeEvent):
        if event.value is None:
            event.user.reset_snooze()
            return

        if isinstance(event.value, str):
            amount, unit = event.value.split(" ")
            duration = float(amount)

            unit = unit.rstrip("s")

            if unit.endswith("Min"):
                duration *= 60
            elif unit.endswith("Hour"):
                duration *= 60 * 60
            elif unit.endswith("Day"):
                duration *= 24 * 60 * 60

            event.user.snooze_for(duration)
            return

        if isinstance(event.value, (int, float)):
            event.user.snooze_for(event.value)
            return

    def handle_specific_snooze_event(self, event: UserSettingsChangedEvent):
        """Handle specific event type snoozes."""
        if event.settings_type == UserSettingsType.SNOOZE_SPECIFIC:
            event.user.set_event_type_snoozed(event.settings_value, event.value)
            return

        if event.settings_type == UserSettingsType.SNOOZE_SENSOR:
            event.user.set_sensor_snoozed(event.settings_value, event.value)
            return
