from logging_config import logger

from sinks.base import NotificationSink
from users import User


class ConsoleSink(NotificationSink):

    def send(
        self,
        user: User,
        message: str,
        payload: dict | bytes,
        silent: bool,
        pin: bool = False,
    ):
        if isinstance(payload, bytes):
            logger.info(f"{user=!s} {message=} payload=<<BYTES>> {silent=}")
        else:
            logger.info(f"{user=!s} {message=} {payload=} {silent=}")
