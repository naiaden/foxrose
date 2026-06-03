from events.event import Event, color_wrap
from enum import Enum, auto
import time

from dataclasses import dataclass, field

from colorama import Fore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class DeviceEvent(Event):
    _SS: str = field(default=f"{Fore.GREEN}", init=False, repr=False)

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] DeviceEvent"

@dataclass(frozen=True)
class BatteryEvent(DeviceEvent):
    def __init__(self, device, percentage):
        super().__init__()

        device : str
        percentage : int

    # def handle(self, system):
    #     if self.percentage < 10:
    #         LowBatteryEvent(device, percentage).handle(system)

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] BatteryEvent [{self.device}]: {self.percentage}%)"

@dataclass(frozen=True)
class LowBatteryEvent(BatteryEvent):

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] LowBatteryEvent [{self.device}]: {self.percentage}%)"
