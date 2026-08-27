import time

from functools import wraps
from colorama import Fore, Style

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Event:
    _create_time: float = field(default_factory=time.time, init=False, repr=False)

    _SS: str = field(default=f"{Fore.CYAN}", init=False, repr=False)
    _SE: str = field(default=f"{Style.RESET_ALL}", init=False, repr=False)

    @property
    def create_time_str(self) -> str:
        return f"{time.ctime(self._create_time)}"

    def __str__(self) -> str:
        return f"[{self.create_time_str}] Event"


def color_wrap(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        original_string = func(self, *args, **kwargs)
        return f"{self._SS}{original_string}{self._SE}"

    return wrapper
