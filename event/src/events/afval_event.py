from events.event import Event, color_wrap
from dataclasses import dataclass


@dataclass(frozen=True)
class AfvalEvent(Event):
    _SS = ""

    message: str

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] AfvalEvent: [{self.message}]"
