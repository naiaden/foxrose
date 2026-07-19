import os
from pathlib import Path
from dotenv import load_dotenv

# Import and setup centralized logging (this also imports logger)
from logging_config import logger

from sinks.telegram import TelegramSink
from sinks.console import ConsoleSink

from routing.router import NotificationRouter
from routing.event_handlers import (
    AfvalEventHandler,
    DoorcardEventHandler,
    PresenceDetectionEventHandler,
    CameraDetectionEventHandler,
    DeviceEventHandler,
    SnoozeEventHandler,
    ModeToggleEventHandler,
    UserSettingChangedEventHandler,
    TemperatureEventHandler,
    SystemEventHandler,
)
from handlers.mqtt import MQTTMainDispatcher, MQTTFrigateDispatcher
from state import StateManager
from handlers.telegram import FoxRoseHandler
from config import load_config


def main():
    # Load environment variables from .env file
    base_dir = Path(__file__).resolve().parent.parent
    load_dotenv(base_dir / ".env")

    logger.info("Initialising FOXROSE")

    # Load configuration from YAML file
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    config = load_config(config_path)

    # Get secrets from environment
    telegram_token = os.environ.get("BOT_TOKEN")
    if not telegram_token:
        logger.critical("Missing BOT_TOKEN environment variable")
        return

    # Build state manager from config
    state_manager = StateManager(
        users=config.users,
        valid_doorcards=set(config.valid_doorcards),
        sensors=config.sensors,
        cameras=config.frigate_cameras,
        thermometers=config.thermometers,
        presence_window_seconds=config.presence_window_seconds,
    )

    notification_sinks = [TelegramSink(bot_token=telegram_token), ConsoleSink()]

    router = NotificationRouter(state_manager=state_manager, sinks=notification_sinks)

    for handler in (
        AfvalEventHandler,
        DoorcardEventHandler,
        PresenceDetectionEventHandler,
        CameraDetectionEventHandler,
        DeviceEventHandler,
        SnoozeEventHandler,
        ModeToggleEventHandler,
        UserSettingChangedEventHandler,
        TemperatureEventHandler,
        SystemEventHandler,
    ):
        handler(router, state_manager)

    MQTTMainDispatcher(
        state_manager=state_manager, router=router, address=config.mqtt.main_server
    ).connect()
    MQTTFrigateDispatcher(
        state_manager=state_manager, router=router, address=config.mqtt.frigate_server
    ).connect()

    bot = FoxRoseHandler(state_manager, router, telegram_token, config)
    bot.run()

    logger.info("Initialization complete. Starting application block...")


if __name__ == "__main__":
    main()
