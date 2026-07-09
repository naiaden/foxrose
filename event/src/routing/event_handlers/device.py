"""Handler for device events."""

from events import DeviceEvent, BatteryEvent, LowBatteryEvent


class DeviceEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(DeviceEvent, self.handle_device_event)

    def handle_device_event(self, event: DeviceEvent):
        if isinstance(event, BatteryEvent):
            if event.percentage < 10:
                self.router.route_event(LowBatteryEvent(event.device, event.percentage))
