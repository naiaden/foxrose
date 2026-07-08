from events.event import Event, color_wrap
from enum import Enum, auto
import time
import datetime

from dataclasses import dataclass, field

from colorama import Fore
from logging_config import logger

from sensors import Sensor, SensorType

@dataclass(frozen=True)
class DetectionEvent(Event):

    _SS = f"{Fore.YELLOW}"

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] DetectionEvent"


# @dataclass(frozen=False)
# class CameraActiveEvent(DetectionEvent):
#     camera:str
#     event_id :str

#     updates: list
#     # update()

#     _SS = f"{Fore.RED}"

#     @color_wrap
#     def __str__(self):
#         return f"[{self.create_time_str}] CameraActiveEvent [{self.event_id}]: {self.camera} (last update: {self.last_update}/#{len(self.updates)})"

#     # def update(self):
        

#     #     self.last_update = time.time()
#     #     self.updates.append(self.last_update)

#     #     logger.info(self)


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
        self.decay_time = 10*60

        self.triggering_events = set()

    def _get_active_time(self):
        current_time = datetime.datetime.now().time()

        night_time_start = datetime.time(0,0)
        night_time_end = datetime.time(6,0)

        if night_time_start <= current_time <= night_time_end:
            return 2

        return 10



    def process(self, system, event_id, camera, msg_payload):
        if event_id not in self.active_events:
            self.active_events[event_id] = CameraActiveEvent(camera, event_id)

        logger.info(f"{len(self.active_events)} active events before pruning")

        self.active_events[event_id].update()

        ## Events past their expiration

        delete_keys = set()
        for _event_id, _event in self.active_events.items():
            if (duration := _event.last_update - _event._create_time) > self.decay_time:
                logger.debug(f"{_event_id} was removed because it was stale for {duration}")
                delete_keys.add(_event_id)
        self.active_events = {k: self.active_events[k] for k in self.active_events.keys() - delete_keys} 

        logger.debug(f"{len(self.active_events)} active events after pruning")

        ## Build evidence for loitering

        cameras_involved = {_event.camera for _event in self.active_events.values()}

        logger.warning(f"Currently activity on {len(cameras_involved)} cameras")

        ## 

        event = self.active_events[event_id]
        event_duration = event.last_update - event._create_time
        confidence = DetectionConfidence.from_duration(event_duration)
        logger.info(f"Loitering confidence for {event_id} is {confidence} "
                     f"because it's been active for {event_duration} seconds in {len(event.updates)} updates.")

        if event_id not in self.triggering_events:
            if confidence == DetectionConfidence.LOITERING or len(cameras_involved) > 1:
                CameraLoiteringEvent(cameras_involved, confidence).handle(system)
                self.triggering_events.add(event_id)

            

@dataclass(frozen=True)
class CameraLoiteringEvent(DetectionEvent):
    cameras_involved : list
    confidence : float

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] CameraLoiteringEvent: {self.cameras_involved} -- confidence: {self.confidence}"

@dataclass(frozen=True)
class CameraDetectionEvent(DetectionEvent):
    camera_name: str
    payload: dict

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] CameraDetectionEvent: {self.camera_name}"

@dataclass(frozen=True)
class PresenceDetectionEvent(DetectionEvent):
    device:str
    
    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] PresenceDetectionEvent on {self.device}"

@dataclass(frozen=True)
class IndoorPresenceDetectionEvent(PresenceDetectionEvent):
    device: Sensor

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] IndoorPresenceDetectionEvent on {self.device}"


@dataclass(frozen=True)
class OutdoorPresenceDetectionEvent(PresenceDetectionEvent):
    device: Sensor

    @color_wrap
    def __str__(self):
        return f"[{self.create_time_str}] OutdoorPresenceDetectionEvent on {self.device}"
    
