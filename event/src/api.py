import paho.mqtt.client as mqtt
import json
import requests
import os
import datetime
import io
from enum import StrEnum
import logging

from systems.telegram import send_to_telegram, build_menu_keyboard, start, menu_callback, global_debug_inspector, error_handler

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


class DoorBellLocation(StrEnum):
    ACHTERDEUR = "9901"
    VOORDEUR = "9903"

ACHTERDEUR_IP = os.environ['ACHTERDEUR_IP']
ACHTERDEUR_ACCOUNT = os.environ['ACHTERDEUR_ACCOUNT']
ACHTERDEUR_PASSWORD = os.environ['ACHTERDEUR_PASSWORD']

VOORDEUR_IP = os.environ['VOORDEUR_IP']
VOORDEUR_ACCOUNT = os.environ['VOORDEUR_ACCOUNT']
VOORDEUR_PASSWORD = os.environ['VOORDEUR_PASSWORD']

DOORBELL_TOPIC = os.environ['DOORBELL_TOPIC']
MQTT_SERVER = os.environ['mqtt_server']
MQTT_SERVER_SECOND = os.environ['mqtt_server_second']
LIGHTAPI_SERVER = os.environ['lightapi_server']
VALID_DOORCARDS = os.environ['VALID_DOORCARDS'].split(',')

BOT_TOKEN = os.environ['BOT_TOKEN']
BOT_TOPIC = os.environ['BOT_NAME']

FRIGATE_CAMERAS = os.environ['FRIGATE_CAMERAS'].split(',')

mqttc = None
mqtts = None

doorbell_settings = {
    DoorBellLocation.ACHTERDEUR: {'endpoint': f'http://{ACHTERDEUR_IP}/cgi-bin/snapshot.cgi', 
                                  'auth': requests.auth.HTTPDigestAuth(ACHTERDEUR_ACCOUNT, ACHTERDEUR_PASSWORD)},
    DoorBellLocation.VOORDEUR: {'endpoint': f'http://{VOORDEUR_IP}/cgi-bin/snapshot.cgi', 
                                  'auth': requests.auth.HTTPDigestAuth(VOORDEUR_ACCOUNT, VOORDEUR_PASSWORD)}
}

class NotificationSystem:
    def __init__(self):
        self.allowed_users = [int(uid.strip()) for uid in os.environ['ALLOWED_USERS'].split(',')]
        self.user_prefs_cache = {user_id: {cam: False for cam in FRIGATE_CAMERAS} for user_id in self.allowed_users}
        

notification_system = NotificationSystem()

def get_snapshot(location):
    r = requests.get(doorbell_settings[location]['endpoint'], auth=doorbell_settings[location]['auth'])
    logger.debug(r)

    with open(fn := f'{location}-{datetime.datetime.now()}.jpg', 'wb') as f:
        f.write(r.content)

    return fn

def notify_person(msg):
    logger.debug(f"Person payload: {msg.payload}")
    try:
        requests.put(f"https://ntfy.sh/{DOORBELL_TOPIC}", data=msg.payload, headers={"Filename": "snapshot.jpg", "ContentType": "image/jpeg"})
    except Exception as e:
        logger.error(f"A critical error occurred: {e}", exc_info=True)
    
def get_user_preferences(user_id: int) -> dict:
    return notification_system.user_prefs_cache.get(user_id, {cam: False for cam in FRIGATE_CAMERAS})

def toggle_camera_pref(user_id: int, camera: str):
    prefs = get_user_preferences(user_id)
    current_state = prefs.get(camera, False)

    new_payload = "1" if not current_state else "0"
    topic = f"{BOT_TOPIC}/bot/users/{user_id}/cameras/{camera}"

    mqttc.publish(topic, payload=new_payload, qos=1, retain=True)


def doorbell(msg):
    payload = json.loads(msg.payload.decode())
    location = DoorBellLocation(payload['Data']['UserID'])

    fn = get_snapshot(location)

    requests.put(f'https://ntfy.sh/{DOORBELL_TOPIC}',
        data=open(fn, 'rb'),
        headers={ "Filename": fn })

# def doorbell(msg):
#     requests.post(f'http://{settings["loxone_server"]}/dev/sps/io/mqtt_deurbel_gaat/1')

def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected to main with result code {reason_code}")
    client.subscribe("DahuaVTO/DoorCard/Event/#") 
    client.subscribe("DahuaVTO/Invite/Event/#") 
    client.subscribe(f"{BOT_TOPIC}/bot/users/+/cameras/+")

def on_message(client, userdata, msg):
    logger.info(msg.topic+" "+str(msg.payload))

    if msg.topic.startswith("{BOT_TOPIC}/bot/users/"):
        try:
            parts = msg.topic.split("/")
            user_id = int(parts[3])
            camera = parts[5]
            enabled = msg.payload.decode().strip() == "1"

            if user_id in notification_system.allowed_users and user_id not in notification_system.user_prefs_cache:
                notification_system.user_prefs_cache[user_id] = {cam: False for cam in FRIGATE_CAMERAS}

            notification_system.user_prefs_cache[user_id][camera] = enabled
            logger.debug(f"Cache updated via MQTT: User {user_id} -> {camera} = {enabled}")
        except Exception as e:
            logger.error(f"Error parsing bot preference topic: {e}")
        return

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
    #notify_person(msg)

    parts = msg.topic.split('/')
    camera_name = parts[1]
    send_to_telegram(notification_system, msg.payload, camera_name)

logger.info('init')

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.enable_logger(logger)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqtts = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtts.on_connect = on_connect_second
mqtts.on_message = on_message_second

application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("camera", start))
application.add_handler(MessageHandler(filters.ALL, global_debug_inspector))
application.add_handler(CallbackQueryHandler(menu_callback))
application.add_error_handler(error_handler)


logger.info(f"{MQTT_SERVER=}")
logger.info(f"{MQTT_SERVER_SECOND=}")
logger.info(f"{DOORBELL_TOPIC=}")

try:
    mqttc.connect(MQTT_SERVER, 1883, 60)
    mqttc.loop_start()
    mqtts.connect(MQTT_SERVER_SECOND, 1883, 60)
    mqtts.loop_start()

    application.run_polling(drop_pending_updates=True)

    logger.info("System running")


    #while True:
    #    import time
    #    time.sleep(1)
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
