import paho.mqtt.client as mqtt
import json
import requests
import os
import logging
from systems.telegram import send_to_telegram, FoxRoseHandler
from systems.dahua import get_snapshot
from modes import Mode

import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

logger.info("start foxrose event handler")


def doorcard(msg):
    
    payload = json.loads(msg.payload.decode())

    DoorCardEvent(payload['Data']['Number']).handle(system)


def from_bot(msg):
    parts = msg.topic.split("/")
    user_id = int(parts[3])
    camera = parts[5]
    enabled = msg.payload.decode().strip() == "1"

    UserSettingsChangedEvent(user_id, UserSettingsType.CAMERA_PREFERENCE, camera, enabled).handle(system)


from events import *

def person_detected(msg):
    parts = msg.topic.split('/')
    camera_name = parts[1]
    
    CameraDetectionEvent(camera_name, msg.payload).handle(system)

def event_activity(msg):
    event_id = "123"
    CameraActiveEventHandler.process(system, event_id, camera, msg)
    
MQTT_SERVER = os.environ['mqtt_server']
MQTT_SERVER_SECOND = os.environ['mqtt_server_second']
LIGHTAPI_SERVER = os.environ['lightapi_server']

mqttc = None
mqtts = None

from systems.camera import CameraSystem
from systems.notification import NotificationSystem

class System:
    def __init__(self):
        self.allowed_users = [int(uid.strip()) for uid in os.environ['ALLOWED_USERS'].split(',')]
        self.valid_doorcards = os.environ['VALID_DOORCARDS'].split(',')
        self.key_map = json.loads(os.environ.get('KEY_MAP', '{}'))

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
