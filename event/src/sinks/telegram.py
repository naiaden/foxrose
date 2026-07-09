import requests


import io

from logging_config import logger

from sinks.base import NotificationSink
from users import User


class TelegramSink(NotificationSink):
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def send(
        self,
        user: User,
        message: str,
        payload: dict | bytes,
        silent: bool,
        pin: bool = False,
    ):
        if isinstance(payload, bytes):
            return self.send_image(user.telegram_user_id, message, payload, silent)
        else:
            self.send_message(user.telegram_user_id, message, silent, pin)

    def send_message(self, user_id: int, message: str, silent: bool, pin: bool = False):
        logger.info(f"[Telegram Bot] Sending to {user_id} (Silent={silent}): {message}")

        chat_id = user_id

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        data = {"chat_id": chat_id, "text": message, "disable_notification": silent}

        try:
            response = requests.post(url, data=data)
            logger.debug(f"Sent text message to {chat_id}: {response.status_code}")

            response_json = response.json()
            if response_json.get("ok"):
                msg_id = response_json["result"]["message_id"]
                if pin:
                    self.pin_message(chat_id=chat_id, message_id=msg_id)
                return msg_id
            else:
                logger.error(f"Telegram API Error: {response_json.get('description')}")
                return None
        except Exception as e:
            logger.error(f"Error sending text to Telegram: {e}")
            return None

    def send_image(self, user_id: int, message: str, image_bytes: bytes, silent: bool):
        chat_id = user_id
        # logger.debug(f"{chat_id=}, {camera_name=}")

        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"

        files = {"photo": ("snapshot.jpg", io.BytesIO(image_bytes), "image/jpeg")}
        data = {
            "chat_id": chat_id,
            "caption": f"{message}",
            "disable_notification": silent,
        }

        try:
            response = requests.post(url, files=files, data=data)
            logger.debug(f"Sent snapshot: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending to Telegram: {e}")

    def pin_message(
        self, chat_id: int, message_id: int, disable_notification: bool = False
    ):
        logger.info(f"[Telegram Bot] Pinning message {message_id} in chat {chat_id}")

        url = f"https://api.telegram.org/bot{self.bot_token}/pinChatMessage"

        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification,
        }

        try:
            response = requests.post(url, data=data)
            response_json = response.json()

            if response_json.get("ok"):
                logger.debug(f"Successfully pinned message {message_id}")
                return True
            else:
                logger.error(
                    f"Failed to pin message: {response_json.get('description')}"
                )
                return False
        except Exception as e:
            logger.error(f"Error pinning message: {e}")
            return False
