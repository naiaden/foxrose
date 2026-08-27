"""Handler for system events."""

from events import SystemEvent


class SystemEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(SystemEvent, self.handle_system_event)

    def handle_system_event(self, event: SystemEvent):
        """Handle system events and route to sinks."""
        # Route all system events to sinks
        for sink in self.router.sinks:
            sink.send(event)
