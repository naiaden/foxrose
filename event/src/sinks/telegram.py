from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import logging
import requests
from modes import Mode

from events.change_event import UserModeToggleEvent, UserSettingsChangedEvent, UserSettingsType

import io

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

from sinks.base import NotificationSink
from users import User

logger = logging.getLogger(__name__)

class TelegramSink(NotificationSink):
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def send(self, user: User, message: str, payload: dict|bytes, silent: bool):
        if isinstance(payload, bytes):
            return send_image(user_id, message, payload, silent)
        else: #if isinstance(payload, dict):
            return send_message(user_id, message, payload, silent)

    def send_message(self, user: User, message: str, payload: dict, silent: bool):
        # Your actual Telegram API call logic here
        logger.info(f"[Telegram Bot] Sending to {user_id} (Silent={silent}): {message}")

    def send_image(self, user: User, message: str, image_bytes: bytes, silent: bool):
        chat_id = user.telegram_id
        logger.debug(f"{chat_id=}, {camera_name=}")

        url =  f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"


        files = {'photo': ('snapshot.jpg', io.BytesIO(image_bytes), 'image/jpeg')}
        data = {'chat_id': chat_id, 'caption': f"{message}", 'disable_notification': silent}
        
        try:
            response = requests.post(url, files=files, data=data)
            logging.debug(f"Sent snapshot from {camera_name}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error sending to Telegram: {e}")

