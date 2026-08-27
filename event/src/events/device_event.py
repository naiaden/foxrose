from events.event import Event, color_wrap
from dataclasses import dataclass, field
from colorama import Fore


@dataclass(frozen=True)
class DeviceEvent(Event):
    _SS: str = field(default=f"{Fore.GREEN}", init=False, repr=False)

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] DeviceEvent"


@dataclass(frozen=True)
class BatteryEvent(DeviceEvent):
    device: str
    percentage: int

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] BatteryEvent [{self.device}]: {self.percentage}%)"


@dataclass(frozen=True)
class LowBatteryEvent(BatteryEvent):
    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] LowBatteryEvent [{self.device}]: {self.percentage}%)"


@dataclass(frozen=True)
class TemperatureEvent(DeviceEvent):
    device: str
    temperature: float

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] TemperatureEvent [{self.device}]: {self.temperature}*)"


@dataclass(frozen=True)
class TemperatureRisingEvent(DeviceEvent):
    # history : list[float]

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] TemperatureRisingEvent [{self.device}]: {self.temperature}*)"


@dataclass(frozen=True)
class HighTemperatureEvent(DeviceEvent):
    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] HighTemperatureEvent [{self.device}]: {self.temperature}*)"
