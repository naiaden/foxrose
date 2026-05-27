import time
from enum import Enum
import logging
import requests
from modes import Mode
from systems.telegram import send_to_telegram, FoxRoseHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class Event:
    def __init__(self):
        self._create_time = time.time()

    def handle(self, system):
        pass

class DoorCardEvent(Event):
    def __init__(self, card_number):
        super.__init__(self)
        self.card_number = card_number

    def handle(self, system):
        if self.card_number in system.valid_doorcards:
            print("LAMPJES")
            requests.post(f'http://{LIGHTAPI_SERVER}:8555/home/active/toggle')

        for user_id, keys in system.key_map.items():
            if self.card_number in keys:

                UserSettingsChangedEvent(user_id, UserSettingsType.MOOD, )

class DetectionEvent(Event):
    def __init__(self):
        super.__init__(self)

class CameraDetectionEvent(DetectionEvent):
    def __init__(self, camera_name, payload):
        super.__init__(self)
        self.camera_name = camera_name
        self.payload = payload

    def handle(self, system):
        target_chat_ids = []
        
        for user_id, camera_settings in system.notification_system.user_prefs_cache.items():
            logger.info(f"{user_id=}, {camera_settings=}, {system.allowed_users=}, {system.notification_system.is_user_snoozed(user_id)=}")
            if user_id in system.allowed_users and camera_settings[camera_name] and not system.notification_system.is_user_snoozed(user_id):
                logger.info(f"{user_id=} added to {target_chat_ids=}")
                target_chat_ids.append(user_id)
        
        for chat_id in target_chat_ids:
            send_to_telegram(chat_id, self.payload, self.camera_name)

class PresenceDetectionEvent(DetectionEvent):
    def __init__(self):
        super.__init__(self)

class IndoorPresenceDetectionEvent(PresenceDetectionEvent):
    def __init__(self):
        super.__init__(self)

class OutdoorPresenceDetectionEvent(PresenceDetectionEvent):
    def __init__(self):
        super.__init__(self)

class ChangeEvent(Evemt):
    def __init__(self):
        super.__init__(self)

class SettingsChangedEvent(ChangeEvent):
    def __init__(self):
        super.__init__(self)

    def handle(self, system):
        pass

class UserSettingsType(Enum):
    CAMERA_PREFERENCE
    MODE
    SNOOZE

class UserSettingsChangedEvent(ChangeEvent):
    def __init__(self, user_id, settings_type, settings_value=None, value=None):
        super.__init__(self)
        self.user_id = user_id
        self.settings_type = settings_type
        self.settings_value = settings_value
        self.value = value

    def handle(self, system):
        if self.settings_type == UserSettingsType.CAMERA_PREFERENCE:
            system.notification_system.set_user_preference(self.user_id, self.settings_value, self.value)

class UserSnoozeEvent(UserSettingsChangedEvent):
    def __init__(self, user_id, snooze_time):
        super.__init__(self, UserSettingsType.SNOOZE)
        self.value = snooze_time

    def handle(self, system):
        if self.value == None:
            self.system.notification_system.reset_user_snooze(self.user_id)
            return
        
        if isinstance(self.value, str):
            amount, unit = self.value.split(' ')
            duration = amount
            
            unit = unit.rstrip('s')

            if unit.endswith('Min'):
                duration *= 60
            elif unit.endswith("Hour"):
                duration *= 60 * 60
            elif unit.endswith("Day"):
                duration *= 24 * 60 * 60

            self.system.notification_system.set_user_snooze(user_id, duration)
            return

        if isinstance(self.value, (int, float)):
            self.system.notification_system.set_user_snooze(user_id, self.value)
            return


class UserModeToggleEvent(UserSettingsChangedEvent):
    def __init__(self, user_id, value=None):
        super.__init__(self, user_id, UserSettingsType.MODE)

        self.value = value  or not system.notification_system.get_user_mode(user_id)

    def handle(self, system):
        system.notification_system.set_user_mode(self.user_id, self.value)