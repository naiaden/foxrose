import paho.mqtt.client as mqtt
import json
import requests

from event.src.config import settings

def doorcard(msg):
    payload = json.loads(msg.payload.decode())
    if payload['Data']['Number'] in settings['valid_doorcards']:
        requests.post(f'http://{settings["lightapi_server"]}:8555/home/active/toggle')


def doorbell(msg):
    requests.post(f'http://{settings["loxone_server"]}/dev/sps/io/mqtt_deurbel_gaat/1')

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("DahuaVTO/DoorCard/Event/#")

def on_message(client, userdata, msg):
    match msg.topic:
        case "DahuaVTO/DoorCard/Event":
            doorcard(msg) 
    # print(msg.topic+" "+str(msg.payload))

print( 'mqtt connection')

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message



mqttc.connect(settings['mqtt_server'], 1883, 60)


mqttc.loop_forever()



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