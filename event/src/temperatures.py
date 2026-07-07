# from state import StateManager
from enum import Enum

from datetime import datetime, timedelta

class TemperatureTrend(Enum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"

    def as_emoji(self):
        mapping = {
            TemperatureTrend.RISING: "🔴",
            TemperatureTrend.FALLING: "🔵",
            TemperatureTrend.STABLE: "⚪"
        }
        return mapping[self]


# Based on Time-Windowed Moving Average
class TemperatureTracker:
    def __init__(self, device: str, name: str, windows_minutes:int = 5, max_allowed_jump:float=3.0, buffer:float=0.2):
        self.device = device
        self.name = name
        self.history = []

        self.window_duration = timedelta(minutes=windows_minutes)
        self.max_allowed_jump = max_allowed_jump
        self.buffer = buffer

        self.reading = TemperatureTrend.STABLE
        self.current_avg = None

    def add_reading(self, temp: float, timestamp: datetime) ->TemperatureTrend:
        ts = datetime.fromtimestamp(timestamp)
        
        cutoff = ts - self.window_duration
        self.history = [(t, v) for t, v in self.history if t > cutoff]

        if not self.history:
            self.history.append((ts, temp))
            self.reading = TemperatureTrend.STABLE
            return TemperatureTrend.STABLE
        
        self.current_avg = sum(v for t, v in self.history) / len(self.history)
        if abs(temp - self.current_avg) > self.max_allowed_jump:
            # It's a fluke! Ignore this reading completely
            self.reading = TemperatureTrend.STABLE
            return TemperatureTrend.STABLE

        oldest_temp = self.history[0][1]

        self.history.append((ts, temp))

        if temp > (oldest_temp + self.buffer):
            self.reading = TemperatureTrend.RISING
            return TemperatureTrend.RISING
        elif temp < (oldest_temp - self.buffer):
            self.reading = TemperatureTrend.FALLING
            return TemperatureTrend.FALLING
        self.reading = TemperatureTrend.STABLE
        return TemperatureTrend.STABLE


class TemperatureSystem:
    def __init__(self, state, thermometers):#: StateManager):
        self.state = state
        self.mapping = thermometers

        self.trackers = {}
    
    def get_tracker(self, device:str) -> TemperatureTracker:
        name = self.mapping.get(device, device[-5:])
        return self.trackers.setdefault(device, TemperatureTracker(device, name))
    
    def add_reading(self, device:str, temp:float, timestamp: datetime) -> TemperatureTrend:
        reading = self.get_tracker(device).add_reading(temp, timestamp)
        # if TemperatureTrend.RISING == reading:
        #     self.state.route_event(TemperatureRisingEvent())
    
    def get_latest_readings(self):
        r = []
        for t in self.trackers.values():
            r.append((t.name, t.history[-1], t.reading, t.current_avg))
        return r