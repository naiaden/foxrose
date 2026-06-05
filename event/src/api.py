import paho.mqtt.client as mqtt
import json
import requests
import os
import logging
from systems.telegram import FoxRoseHandler
from systems.dahua import get_snapshot
from modes import Mode

from events.change_event import UserSettingsChangedEvent, UserSettingsType
from events.detection_event import CameraActiveEventHandler, CameraDetectionEvent
from events.doorcard_event import DoorCardEvent
from events.device_event import BatteryEvent, LowBatteryEvent
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

logger.info("start foxrose event handler")




from events import *


MQTT_SERVER = os.environ['mqtt_server']
MQTT_SERVER_SECOND = os.environ['mqtt_server_second']


mqttc = None
mqtts = None

from systems.camera import CameraSystem
from systems.notification import NotificationSystem

class System:
    def __init__(self):
        self.allowed_users = [int(uid.strip()) for uid in os.environ['ALLOWED_USERS'].split(',')]
        self.valid_doorcards = os.environ['VALID_DOORCARDS'].split(',')
        self.key_map = {k: v.split(',') for x in os.environ['KEY_MAP'].split(';') for k, v in [x.split(':')]}

        self.camera_system = CameraSystem()
        self.camera_active_event_handler = CameraActiveEventHandler()
        self.notification_system = NotificationSystem(self.allowed_users, self.camera_system.captured_cameras, mqttc)


system = System()

# def doorbell(msg):
#     requests.post(f'http://{settings["loxone_server"]}/dev/sps/io/mqtt_deurbel_gaat/1')




    


    
        

    

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
