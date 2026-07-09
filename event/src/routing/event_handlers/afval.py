"""Handler for waste collection (Afval) events."""

from events import AfvalEvent


class AfvalEventHandler:
    def __init__(self, router, state_manager):
        self.router = router
        self.state = state_manager

        self.router.subscribe(AfvalEvent, self.handle_afval_event)

    def handle_afval_event(self, event: AfvalEvent):
        for user in self.state.users.get_all_users():
            for sink in self.router.sinks:
                sink.send(user, event.message, None, True, pin=True)
