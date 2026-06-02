import time
import os
from modes import Mode

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)



class NotificationSystem:

    def __init__(self, users, cameras, publish_client):

        self.user_prefs_cache = {user_id: {cam: False for cam in cameras} for user_id in users}
        self.user_snoozed_until = {user_id: 0 for user_id in users}
        self.user_mode = {user_id: Mode.STANDARD for user_id in users}
        
        self.mqtt_topic = os.environ['BOT_NAME']
        self.mqtt_publish_server = publish_client

    def get_user_mode(self, user_id) -> Mode:
        return self.user_mode[user_id]

    def set_user_mode(self, user_id, mode):
        self.user_mode[user_id] = mode

    def get_user_preferences(self, user_id: int) -> dict:
        return self.user_prefs_cache[user_id]

    def get_user_preference(self, user_id:int, camera:str) -> bool:
        return self.user_prefs_cache[user_id].get(camera, False)

    def set_user_preference(self, user_id: int, camera: str, value: bool):
        current_value = self.get_user_preference(user_id, camera)

        if current_value != value:
            self.user_prefs_cache[user_id][camera] = value

            topic = f"{self.mqtt_topic}/bot/users/{user_id}/cameras/{camera}"
            payload = "1" if value else "0"
            self._publish_retained(topic, payload)

    def is_user_snoozed(self, user_id):
        if snoozed_until := self.user_snoozed_until[user_id]:
            return time.time() <= snoozed_until
    
    def _set_user_snooze_abs(self, user_id, snooze_time):
        self.user_snoozed_until[user_id] = snooze_time

    def set_user_snooze(self, user_id, snooze_time):
        self._set_user_snooze_abs(user_id, time.time() + snooze_time)

    def reset_user_snooze(self, user_id):
        self._set_user_snooze_abs(user_id, 0)

    def _publish_retained(self, topic, payload):
        if self.mqtt_publish_server and self.mqtt_publish_server.is_connected():
            self.mqtt_publish_server.publish(topic, payload=payload, qos=1, retain=True)
        else:
            logger.error("❌ Primary MQTT client is offline. Configuration state could not be sent.")
    
    def is_silent(self):
        return False

    # STANDARD = ModeDetails("All", "🌐 All")
    # AWAY = ModeDetails("Away", "🧳 Away") # Trigger on all events, including presence detection
    # NIGHT = ModeDetails("Night", "🌙 Night") # Ignore notifications that make sense, such as presence in bed room
    # AT_HOME = ModeDetails("At Home", "🏠 At Home") # Ignore inside presence
    

    # notify silent priority(1-5)
    def event_processing_arbiter(self, event, user_id):
        if snooze := self.is_user_snoozed(user_id):
            return snooze

        if self.get_user_mode(user_id) == Mode.AT_HOME:
            if isinstance(event, CameraDetectionEvent) and self.get_user_preference(user_id, event.camera_name):
                return (True, False, "high")



        elif self.get_user_mode(user_id) == Mode.AWAY:
            if isinstance(event, CameraDetectionEvent) and self.get_user_preference(user_id, event.camera_name):
                return (True, False, "high")



        elif self.get_user_mode(user_id) == Mode.NIGHT:
            if isinstance(event, CameraDetectionEvent) and self.get_user_preference(user_id, event.camera_name):
                return (True, False, "high")



        else: # self.get_user_mode(user_id) == Mode.STANDARD:
            if isinstance(event, CameraDetectionEvent) and self.get_user_preference(user_id, event.camera_name):
                return (True, False, "high")
