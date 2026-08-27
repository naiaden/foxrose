from events.event import Event, color_wrap
from dataclasses import dataclass, field
from colorama import Fore


@dataclass(frozen=True)
class SystemEvent(Event):
    _SS: str = field(default=f"{Fore.MAGENTA}", init=False, repr=False)

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] SystemEvent"


@dataclass(frozen=True)
class HighCPUEvent(SystemEvent):
    hostname: str
    cpu_percentage: float
    threshold: float

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] HighCPUEvent [{self.hostname}]: {self.cpu_percentage}% (threshold: {self.threshold}%)"


@dataclass(frozen=True)
class HighSwapUsageEvent(SystemEvent):
    hostname: str
    swap_percentage: float
    threshold: float

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] HighSwapUsageEvent [{self.hostname}]: {self.swap_percentage}% (threshold: {self.threshold}%)"


@dataclass(frozen=True)
class HighTmpUsageEvent(SystemEvent):
    hostname: str
    tmp_percentage: float
    threshold: float
    path: str

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] HighTmpUsageEvent [{self.hostname}]: {self.tmp_percentage}% on {self.path} (threshold: {self.threshold}%)"
