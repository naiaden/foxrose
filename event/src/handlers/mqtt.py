import paho.mqtt.client as mqtt
from routing.router import NotificationRouter
import logging
from abc import abstractmethod
from typing import Self
import json
from events.change_event import UserSettingsChangedEvent, UserSettingsType
from events.detection_event import CameraActiveEventHandler, CameraDetectionEvent
from events.doorcard_event import DoorCardEvent
from events.device_event import BatteryEvent, LowBatteryEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class MQTTDispatcher:
    def __init__(self, state_manager, router, address):
        self.state = state_manager
        self.router = router
        
        self.ip = address

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.enable_logger(logger)
        self.mqtt_client.on_connect = self.on_connect_handler
        self.mqtt_client.on_message = self.on_message_handler

    def connect(self) -> Self:
        self.mqtt_client.connect(self.ip, 1883, 60)

        logger.info(f"MQTT Dispatcher connected to {self._name}")

        self.mqtt_client.loop_start()

        return self

    @abstractmethod
    def on_connect_handler(self, client, userdata, flags, reason_code, properties=None):
        pass

    @abstractmethod
    def on_message_handler(self, client, userdata, msg):
        pass

class MQTTMainDispatcher(MQTTDispatcher):
    def __init__(self, state_manager, router, address):
        super().__init__(state_manager, router, address)

        self._name = "main"

    def on_connect_handler(self, client, userdata, flags, reason_code, properties=None):
        logger.info(f"Connected to main with result code {reason_code}")
        client.subscribe("DahuaVTO/DoorCard/Event/#") 
        client.subscribe("DahuaVTO/Invite/Event/#") 
        client.subscribe("zigbee2mqtt/+")
        client.subscribe(f"foxrosehip/bot/users/+/cameras/+")

    def on_message_handler(self, client, userdata, msg):
        logger.debug(msg.topic+" "+str(msg.payload))

        if msg.topic.startswith(f"foxrosehip/bot/users/"):
            self._handle_from_bot(msg)
        elif msg.topic.startswith("zigbee2mqtt"):
            self._handle_from_device(msg)

        match msg.topic:
            case "DahuaVTO/DoorCard/Event":
                self._handle_doorcard(msg)
            case "DahuaVTO/Invite/Event":
                pass

    def _handle_doorcard(self, msg):
        payload = json.loads(msg.payload.decode())

        self.router.route_event(DoorCardEvent(payload['Data']['Number']))

    def _handle_from_bot(self, msg):
        parts = msg.topic.split("/")
        user = self.state.user_from_telegram_id(parts[3])
        camera = parts[5]
        enabled = msg.payload.decode().strip() == "1"

        if user:
            self.router.route_event(UserSettingsChangedEvent(user, UserSettingsType.CAMERA_PREFERENCE, camera, enabled))

    def _handle_from_device(self, msg):
        device = msg.topic.split('/')[1]
        payload = json.loads(msg.payload.decode())

        if percentage := payload.get('battery', None):
            self.router.route_event(BatteryEvent(device, battery))


class MQTTFrigateDispatcher(MQTTDispatcher):
    def __init__(self, state_manager, router, address):
        super().__init__(state_manager, router, address)

        self._name = "frigate"


    def on_connect_handler(self, client, userdata, flags, reason_code, properties=None):
        logger.debug(f"Connected to second (frigate) with result code {reason_code}")
        client.subscribe("frigate/+/+/snapshot")
        client.subscribe("frigate/events")

    def on_message_handler(self, client, userdata, msg):
        if msg.topic == "frigate/events":
            self._handle_frigate_event(msg)
        else:
            logger.debug("Person detected: " + msg.topic)

            self._handle_person_detected(msg)

    def _handle_frigate_event(self, msg):
        payload = json.loads(msg.payload.decode())
        # self.router.route_event(system.camera_active_event_handler.process(system, payload["after"]["id"], payload["after"]["camera"], payload))

    def _handle_person_detected(self, msg):
        parts = msg.topic.split('/')
        camera_name = parts[1]
        
        self.router.route_event(CameraDetectionEvent(camera_name, msg.payload))
    