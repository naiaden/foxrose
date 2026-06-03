import logging

from sinks.base import NotificationSink
from users import User

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class ConsoleSink(NotificationSink):

    def send(self, user:User, message: str, payload: dict|bytes, silent: bool):
        logger.info(f"{user=!s} {message=} {payload=} {silent=}")