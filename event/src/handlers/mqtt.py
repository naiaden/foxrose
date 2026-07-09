import paho.mqtt.client as mqtt
from abc import abstractmethod
from typing import Self
import json
from logging_config import logger

from events import (
    AfvalEvent,
    UserSettingsChangedEvent,
    UserSettingsType,
    CameraDetectionEvent,
    PresenceDetectionEvent,
    DoorCardEvent,
    BatteryEvent,
    TemperatureEvent,
)


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
        client.subscribe("foxrosehip/bot/users/+/cameras/+")
        client.subscribe("foxrosehip/afval")

    def on_message_handler(self, client, userdata, msg):
        logger.debug(msg.topic + " " + str(msg.payload))

        if msg.topic.startswith("foxrosehip/bot/users/"):
            self._handle_from_bot(msg)
        elif msg.topic.startswith("zigbee2mqtt"):
            self._handle_from_device(msg)

        match msg.topic:
            case "DahuaVTO/DoorCard/Event":
                self._handle_doorcard(msg)
            case "DahuaVTO/Invite/Event":
                pass
            case "foxrosehip/afval":
                self._handle_afval(msg)

    def _handle_afval(self, msg):
        logger.debug("Afval!")
        self.router.route_event(AfvalEvent(msg.payload))

    def _handle_doorcard(self, msg):
        payload = json.loads(msg.payload.decode())

        self.router.route_event(DoorCardEvent(payload["Data"]["Number"]))

    def _handle_from_bot(self, msg):
        parts = msg.topic.split("/")
        user = self.state.user_from_telegram_id(int(parts[3]))
        camera = parts[5]
        enabled = msg.payload.decode().strip() == "1"

        if user:
            self.router.route_event(
                UserSettingsChangedEvent(
                    user, UserSettingsType.CAMERA_PREFERENCE, camera, enabled
                )
            )

    def _handle_from_device(self, msg):
        device = msg.topic.split("/")[1]
        payload = json.loads(msg.payload.decode())

        if percentage := payload.get("battery", None):
            self.router.route_event(BatteryEvent(device, percentage))

        if temperature := payload.get("temperature", None):
            self.router.route_event(TemperatureEvent(device, temperature))

        if payload.get("presence", None):
            self.router.route_event(PresenceDetectionEvent(device))


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
        json.loads(msg.payload.decode())
        # self.router.route_event(system.camera_active_event_handler.process(system, payload["after"]["id"], payload["after"]["camera"], payload))

    def _handle_person_detected(self, msg):
        parts = msg.topic.split("/")
        camera_name = parts[1]

        self.router.route_event(CameraDetectionEvent(camera_name, msg.payload))
