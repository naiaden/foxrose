from events.event import Event, color_wrap
from enum import Enum, auto
from typing import Optional, Any
from dataclasses import dataclass
from users import User
from colorama import Fore
from logging_config import logger

@dataclass(frozen=True)
class AfvalEvent(Event):
    _SS = f""

    message: str

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] AfvalEvent: [{self.message}]"