import requests
import os
from events.event import Event
from events.change_event import UserModeToggleEvent

LIGHTAPI_SERVER = os.environ['lightapi_server']

class DoorCardEvent(Event):
    def __init__(self, card_number):
        super().__init__()
        self.card_number = card_number

    def handle(self, system):
        # if self.card_number in system.valid_doorcards:
        #     print("LAMPJES")
        #     requests.post(f'http://{LIGHTAPI_SERVER}:8555/home/active/toggle')

        for user_id, keys in system.key_map.items():
            if self.card_number in keys:

                UserModeToggleEvent(user_id )