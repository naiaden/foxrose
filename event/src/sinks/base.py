from abc import ABC, abstractmethod

from users import User

class NotificationSink(ABC):
    @abstractmethod
    def send(self, user: User, message: str, payload: dict|bytes, silent: bool):
        pass