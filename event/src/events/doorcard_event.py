import requests
import os
from events.event import Event, color_wrap
from events.change_event import UserModeToggleEvent

LIGHTAPI_SERVER = os.environ['lightapi_server']

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
class DoorCardEvent(Event):

    card_number: str

    _SS = f"{Fore.MAGENTA}"

    def __str__(self):
        return f"[{self.create_time_str}] DoorCardEvent: {self.card_number}"

    def handle(self, system):
        logger.info(self)
        # if self.card_number in system.valid_doorcards:
        #     print("LAMPJES")
        #     requests.post(f'http://{LIGHTAPI_SERVER}:8555/home/active/toggle')

        # for user_id, keys in system.key_map.items():
        #     if self.card_number in keys:

        #         UserModeToggleEvent(user_id ).handle(system)