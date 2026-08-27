"""Handler for temperature events."""

from events import TemperatureEvent


class TemperatureEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(TemperatureEvent, self.handle_temperature_event)

    def handle_temperature_event(self, event: TemperatureEvent):
        if type(event) is TemperatureEvent:
            self.state.add_temperature_reading(
                event.device, event.temperature, event._create_time
            )
