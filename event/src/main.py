import sys
import os
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
from pathlib  import Path
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent
print(base_dir)

load_dotenv(base_dir / ".env.dev")

from sinks.telegram import TelegramSink
from sinks.console import ConsoleSink

from events.doorcard_event import DoorCardEvent
from events.change_event import UserModeToggleEvent, UserSnoozeEvent

from routing.router import AfvalEventHandler, PresenceDetectionEventHandler, TemperatureEventHandler, UserSettingChangedEventHandler,NotificationRouter, DoorcardEventHandler, DeviceEventHandler, DetectionEventHandler, ModeToggleEventHandler, SnoozeEventHandler
from handlers.mqtt import MQTTMainDispatcher, MQTTFrigateDispatcher
from users import UserManager
from state import StateManager
from handlers.telegram import FoxRoseHandler

def main():
    logger.info("Initialising FOXROSE")

    try:
        users = os.environ['USERS']
        allowed_users = os.environ['ALLOWED_USERS'].split(',')
        valid_doorcards = os.environ['VALID_DOORCARDS'].split(',')

        telegram_token = os.environ['BOT_TOKEN']

        mqtt_server_main = os.environ['mqtt_server']
        mqtt_server_frigate = os.environ['mqtt_server_second']
    except KeyError as e:
        logger.critical(f"Missing required environment variable: {e}")
        sys.exit(1)

    

    state_manager = StateManager(
        users=UserManager.from_env_string(users),
        allowed_users=allowed_users,
        valid_doorcards=valid_doorcards
    )

    notification_sinks = [
        # TelegramSink(bot_token=telegram_token)
        ConsoleSink()
    ]

    router = NotificationRouter(
        state_manager=state_manager,
        sinks=notification_sinks
    )

    handler_classes = (
        AfvalEventHandler,
        DoorcardEventHandler,
        PresenceDetectionEventHandler,
        DetectionEventHandler,
        DeviceEventHandler,
        SnoozeEventHandler,
        ModeToggleEventHandler,
        UserSettingChangedEventHandler,
        TemperatureEventHandler,
    )
    handlers = [handler(router, state_manager) for handler in handler_classes]

    main_dispatcher = MQTTMainDispatcher(
        state_manager=state_manager,
        router=router,
        address=mqtt_server_main
    ).connect()
    frigate_dispatcher = MQTTFrigateDispatcher(
        state_manager=state_manager,
        router=router,
        address=mqtt_server_frigate
    ).connect()

    bot = FoxRoseHandler(state_manager, router, telegram_token)
    bot.run()

    

    # mqtt_main = setup_mqtt_client(MQTT_SERVER, dispatcher, on_connect_primary, on_message_handler)
    # mqtts = setup_mqtt_client(MQTT_SERVER_SECOND, dispatcher, on_connect_secondary, on_message_handler)
    
    # router.mqtt_publish_server = mqttc

    #

    logger.info("Initialization complete. Starting application block...")

if __name__=="__main__":
    main()