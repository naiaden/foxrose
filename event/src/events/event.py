import time

from functools import wraps
from colorama import Fore, Style

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class Event:
    def __init__(self):
        self._create_time = time.time()

    def __str__(self):
        return f"[{self.create_time_str}] Event"
    
    _SS = f"{Fore.CYAN}"
    _SE = f"{Style.RESET_ALL}"

    @property
    def create_time_str(self):
        return f"{time.ctime(self._create_time)}"

    def handle(self, system):
        logger.info(self)

def color_wrap(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        original_string = func(self, *args, **kwargs)
        return f"{self._SS}{original_string}{self._SE}"
    return wrapper