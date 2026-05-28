from events.event import Event, color_wrap
from enum import Enum, auto
import time
import datetime
from systems.telegram import send_to_telegram

from colorama import Fore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class DetectionEvent(Event):
    def __init__(self):
        super().__init__()

    _SS = f"{Fore.YELLOW}"

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] DetectionEvent"

    def handle(self):
        logger.info(self)

class CameraActiveEvent(DetectionEvent):
    def __init__(self, camera):
        super().__init__()

        self.camera = camera



        self.updates = []
        self.update()

    _SS = f"{Fore.RED}"

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] CameraActiveEvent: {self.camera} (last update: {self.last_update}/#{len(self.updates)})"

    def update(self):
        

        self.last_update = time.time()
        self.updates.append(self.last_update)

        logger.info(self)

class DetectionConfidence(Enum):
    IGNORE = auto()
    MAYBE = auto()
    LIKELY = auto()
    CONFIDENT = auto()
    LOITERING = auto()

    @classmethod
    def from_duration(cls, seconds):
        if seconds > 10.0:
            return cls.LOITERING
        elif seconds > 5.0:
            return cls.CONFIDENT
        elif seconds > 2.0:
            return cls.LIKELY
        elif seconds >= 1.0:
            return cls.MAYBE
        else:
            return cls.IGNORE

class CameraActiveEventHandler:
    def __init__(self):
        self.active_events = {}
        self.decay_time = 10

    def _get_active_time(self):
        current_time = datetime.datetime.now().time()

        night_time_start = datetime.time(0,0)
        night_time_end = datetime.time(6,0)

        if night_time_start <= current_time <= night_time_end:
            return 2

        return 10



    def process(self, system, event_id, camera, msg_payload):
        if event_id not in self.active_events:
            self.active_events[event_id] = CameraActiveEvent(camera)

        logger.info(f"{len(self.active_events)} active events before pruning")

        self.active_events[event_id].update()

        ## Events past their expiration

        delete_keys = set()
        for _event_id, _event in self.active_events.items():
            if (duration := _event.last_update - _event._create_time) > self._get_active_time(): #self.decay_time:
                logger.info(f"{_event_id} was removed because it was stale for {duration}")
                delete_keys.add(_event_id)
        self.active_events = {k: self.active_events[k] for k in self.active_events.keys() - delete_keys} 

        logger.info(f"{len(self.active_events)} active events after pruning")

        ## Build evidence for loitering

        cameras_involved = {_event.camera for _event in self.active_events.values()}

        logger.info(f"Currently activity on {len(cameras_involved)} cameras")

        confidence = DetectionConfidence.from_duration##FROM ORDERED LIST


        if len(cameras_involved) > 1:
            CameraLoiteringEvent(cameras_involved, confidence).handle(system)

class CameraLoiteringEvent(DetectionEvent):
    def __init__(self, cameras_involved, confidence):
        super().__init__()

        self.cameras_involved = cameras_involved
        self.confidence = confidence

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] CameraLoiteringEvent: {self.cameras_involved} -- confidence: {self.confidence}"

    def handle(self, system):
        logger.info(self)

class CameraDetectionEvent(DetectionEvent):
    def __init__(self, camera_name, payload):
        super().__init__()
        self.camera_name = camera_name
        self.payload = payload

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] CameraDetectionEvent: {self.camera_name}"

    def handle(self, system):
        logger.info(self)

        target_chat_ids = []
        
        for user_id, camera_settings in system.notification_system.user_prefs_cache.items():
            logger.debug(f"{user_id=}, {camera_settings=}, {system.allowed_users=}, {system.notification_system.is_user_snoozed(user_id)=}")
            if user_id in system.allowed_users and camera_settings[self.camera_name] and not system.notification_system.is_user_snoozed(user_id):
                logger.debug(f"{user_id=} added to {target_chat_ids=}")
                target_chat_ids.append(user_id)
        
        for chat_id in target_chat_ids:
            send_to_telegram(chat_id, self.payload, self.camera_name, system.notification_system.is_silent())

class PresenceDetectionEvent(DetectionEvent):
    def __init__(self):
        super().__init__()

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] PresenceDetectionEvent"

    def handle(self, system):
        logger.info(self)

class IndoorPresenceDetectionEvent(PresenceDetectionEvent):
    def __init__(self):
        super().__init__()

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] IndoorPresenceDetectionEvent"

    def handle(self, system):
        logger.info(self)

class OutdoorPresenceDetectionEvent(PresenceDetectionEvent):
    def __init__(self):
        super().__init__()

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] OutdoorPresenceDetectionEvent"
    
    def handle(self, system):
        logger.info(self)