from events.event import Event, color_wrap
from enum import Enum, auto
import time

from colorama import Fore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class DeviceEvent(Event):
    def __init__(self):
        super().__init__()

    _SS = f"{Fore.GREEN}"

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] DeviceEvent"

    def handle(self):
        logger.info(self)

class LowBatteryEvent(Event):
    def __init__(self, device, percentage):
        super().__init__()

        self.device = device
        self.percentage = percentage

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] LowBatteryEvent [{self.device}]: {self.percentage}%)"
