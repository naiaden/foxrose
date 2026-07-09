from events.event import Event, color_wrap
from enum import Enum, auto

from dataclasses import dataclass

from colorama import Fore

from sensors import Sensor


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


# CameraActiveEventHandler and CameraActiveEvent are commented out and not used
# class CameraActiveEventHandler:
#     ...


@dataclass(frozen=True)
class CameraLoiteringEvent(DetectionEvent):
    cameras_involved: list
    confidence: float

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
    device: str

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
        return (
            f"[{self.create_time_str}] OutdoorPresenceDetectionEvent on {self.device}"
        )
