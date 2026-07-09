from events.event import Event
from dataclasses import dataclass
from colorama import Fore


@dataclass(frozen=True)
class DoorCardEvent(Event):

    card_number: str

    _SS = f"{Fore.MAGENTA}"

    def __str__(self):
        return f"[{self.create_time_str}] DoorCardEvent: {self.card_number}"
