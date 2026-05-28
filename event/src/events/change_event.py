from events.event import Event, color_wrap
from enum import Enum, auto

from colorama import Fore
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


class ChangeEvent(Event):
    def __init__(self):
        super().__init__()

    _SS = f"{Fore.CYAN}"

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] ChangeEvent"

    def handle(self, system):
        logger.info(self)

class SettingsChangedEvent(ChangeEvent):
    def __init__(self):
        super().__init__()

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] SettingsChangedEvent"

    def handle(self, system):
        logger.info(self)

class UserSettingsType(Enum):
    CAMERA_PREFERENCE = auto()
    MODE = auto()
    SNOOZE = auto()

class UserSettingsChangedEvent(ChangeEvent):
    def __init__(self, user_id, settings_type, settings_value=None, value=None):
        super().__init__()
        self.user_id = user_id
        self.settings_type = settings_type
        self.settings_value = settings_value
        self.value = value

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserSettingsChangedEvent: {self.user_id} {self.settings_type} {self.settings_value} {self.value}"

    def handle(self, system):
        logger.info(self)
        if self.settings_type == UserSettingsType.CAMERA_PREFERENCE:
            system.notification_system.set_user_preference(self.user_id, self.settings_value, self.value)

class UserSnoozeEvent(UserSettingsChangedEvent):
    def __init__(self, user_id, snooze_time):
        super().__init__(user_id, UserSettingsType.SNOOZE)
        self.value = snooze_time

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserSnoozeEvent: {self.user_id} (snoozed for {self.value})"

    def handle(self, system):
        logger.info(self)

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
        super().__init__(user_id, UserSettingsType.MODE)

        self.value = value

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] UserModeToggleEvent: {self.user_id} -- Toggled: {self.value}"

    def handle(self, system):
        logger.info(self)

        if value is None:
            self.value = not system.notification_system.get_user_mode(user_id)
        system.notification_system.set_user_mode(self.user_id, self.value)