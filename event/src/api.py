import paho.mqtt.client as mqtt
import json
import requests
import os
import logging
from enum import Enum 
from systems.telegram import send_to_telegram, FoxRoseHandler, global_debug_inspector, error_handler
from systems.dahua import get_snapshot
from modes import Mode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

logger.info("start foxrose event handler")


def doorcard(msg):
    
    payload = json.loads(msg.payload.decode())
    if payload['Data']['Number'] in VALID_DOORCARDS:
        print("LAMPJES")
        requests.post(f'http://{LIGHTAPI_SERVER}:8555/home/active/toggle')


def from_bot(msg):
    try:
        parts = msg.topic.split("/")
        user_id = int(parts[3])
        camera = parts[5]
        enabled = msg.payload.decode().strip() == "1"

        system.notification_system.set_user_preference(user_id, camera, enabled)
        logger.debug(f"Cache updated via MQTT: User {user_id} -> {camera} = {enabled}")
    except Exception as e:
        logger.error(f"Error parsing bot preference topic: {e}")
    return

def person_detected(msg):
    parts = msg.topic.split('/')
    camera_name = parts[1]
    
    target_chat_ids = []    

    logger.info(f"{system.notification_system.user_prefs_cache}")
    

    for user_id, camera_settings in system.notification_system.user_prefs_cache.items():
        logger.info(f"{user_id=}, {camera_settings=}, {system.allowed_users=}, {system.notification_system.is_user_snoozed(user_id)=}")
        if user_id in system.allowed_users and camera_settings[camera_name] and not system.notification_system.is_user_snoozed(user_id):
            logger.info(f"{user_id=} added to {target_chat_ids=}")
            target_chat_ids.append(user_id)
    
    for chat_id in target_chat_ids:
        send_to_telegram(chat_id, msg.payload, camera_name)

DOORBELL_TOPIC = os.environ['DOORBELL_TOPIC']
MQTT_SERVER = os.environ['mqtt_server']
MQTT_SERVER_SECOND = os.environ['mqtt_server_second']
LIGHTAPI_SERVER = os.environ['lightapi_server']
VALID_DOORCARDS = os.environ['VALID_DOORCARDS'].split(',')

BOT_TOKEN = os.environ['BOT_TOKEN']

mqttc = None
mqtts = None


class CameraSystem:

    class Camera:
        def __init__(self, name, ip, account, password):
            self.name = name
            self.ip = ip
            self.account = account
            self.password = password

    class Doorbell(Camera):
        def __init__(self, name, ip, account, password, location):
            super().__init__(name, ip, account, password)
            self.location = location

            self.endpoint = f'http://{self.ip}/cgi-bin/snapshot.cgi'
            self.auth = requests.auth.HTTPDigestAuth(account, password)

    def __init__(self):
        self.captured_cameras = os.environ['FRIGATE_CAMERAS'].split(',')
        self.cameras = [
            # Camera("tuinhuis", )
            self.Doorbell("achterdeur", os.environ['ACHTERDEUR_IP'], os.environ['ACHTERDEUR_ACCOUNT'], os.environ['ACHTERDEUR_PASSWORD'], "9901"),
            self.Doorbell("voordeur", os.environ['VOORDEUR_IP'], os.environ['VOORDEUR_ACCOUNT'], os.environ['VOORDEUR_PASSWORD'], "9903"),
        ]

import time



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
            logger.info(f"📤 Sent retain preference to MQTT topic: {topic} -> {payload}")
        else:
            logger.error("❌ Primary MQTT client is offline. Configuration state could not be sent.")

class System:
    def __init__(self):
        self.allowed_users = [int(uid.strip()) for uid in os.environ['ALLOWED_USERS'].split(',')]

        self.camera_system = CameraSystem()

        self.notification_system = NotificationSystem(self.allowed_users, self.camera_system.captured_cameras, mqttc)


system = System()

# def doorbell(msg):
#     requests.post(f'http://{settings["loxone_server"]}/dev/sps/io/mqtt_deurbel_gaat/1')

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected to main with result code {reason_code}")
    client.subscribe("DahuaVTO/DoorCard/Event/#") 
    client.subscribe("DahuaVTO/Invite/Event/#") 
    client.subscribe(f"{system.notification_system.mqtt_topic}/bot/users/+/cameras/+")

def on_message(client, userdata, msg):
    logger.info(msg.topic+" "+str(msg.payload))

    if msg.topic.startswith(f"{system.notification_system.mqtt_topic}/bot/users/"):
        from_bot(msg)

    match msg.topic:
        case "DahuaVTO/DoorCard/Event":
            doorcard(msg) 
        case "DahuaVTO/Invite/Event":
            doorbell(msg)
    
def on_connect_second(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected to second (frigate) with result code {reason_code}")
    client.subscribe("frigate/+/+/snapshot")

def on_message_second(client, userdata, msg):
    logger.info("Person detected: " + msg.topic)

    person_detected(msg)

    
        

    

logger.info('init')

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.enable_logger(logger)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqtts = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtts.on_connect = on_connect_second
mqtts.on_message = on_message_second

bot = FoxRoseHandler(system)


logging.info(f"server: {mqttc}, is connected? {mqttc.is_connected()}")

logger.info(f"{MQTT_SERVER=}")
logger.info(f"{MQTT_SERVER_SECOND=}")
logger.info(f"{DOORBELL_TOPIC=}")

try:
    mqttc.connect(MQTT_SERVER, 1883, 60)
    mqttc.loop_start()
    mqtts.connect(MQTT_SERVER_SECOND, 1883, 60)
    mqtts.loop_start()

    system.notification_system.mqtt_publish_server = mqttc
    logging.info(f"server: {mqttc}, is connected? {mqttc.is_connected()}")

    bot.run()

    logger.info("System running")

except Exception as e:
    logger.error(f"A critical error occurred: {e}", exc_info=True)

except KeyboardInterrupt:
    logger.info("Stopping...")
    mqttc.loop_stop()
    mqtts.loop_stop()



# {
#   "Action": "Pulse",
#   "Code": "Invite",
#   "Data": {
#     "CallID": "4",
#     "IsEncryptedStream": false,
#     "LocaleTime": "2024-09-17 12:52:27",
#     "LockNum": 1,
#     "SupportPaas": false,
#     "TCPPort": 37777,
#     "UTC": 1726573947,
#     "UserID": "9901"
#   },
#   "Index": 0,
#   "deviceType": "DHI-VTO2311R-WP",
#   "serialNumber": "8A008E5PAJC0D73"
# }


# {
#   "Action": "Pulse",
#   "Code": "Hangup",
#   "Data": {
#     "LocaleTime": "2024-09-17 12:52:58",
#     "UTC": 1726573978
#   },
#   "Index": 0,
#   "deviceType": "DHI-VTO2311R-WP",
#   "serialNumber": "8A008E5PAJC0D73"
# }
