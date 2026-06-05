from typing import Dict, List, Any, Set

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

from enum import Enum
from users import UserManager, User
from events.event import Event

from modes import Mode

class StateManager:
    def __init__(self, users:List[User], allowed_users: List[str], valid_doorcards:Set[str]):
        self.users = UserManager(
            users=users,
            allowed_user_names=allowed_users,
        )
        self._valid_doorcards = valid_doorcards

        self._current_house_mode = Mode.AT_HOME
        self._cameras = ["achterdeur", "voordeur", "tuinhuis"]

    def is_doorcard_valid(self, card_id:str):
        return card_id in self._valid_doorcards

    def user_is_allowed(self, user:User) -> bool:
        return self.users.is_allowed(user)

    def user_wants_event(self, user: User, event: Event) -> bool:
        return user.wants_notification(event)

    def get_user_mode(self, user:User) -> Mode:
        return self.users.get_user_mode(user)

    def user_from_telegram_id(self, user_id) -> User:
        return self.users.get_user_from_telegram_id(user_id)
    
    def user_from_doorcard(self, card_id:str):
        return self.users.get_user_from_doorcard(card_id)

