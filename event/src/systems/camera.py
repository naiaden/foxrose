import requests
from typing import Dict

from config import DoorConfig


class Camera:
    def __init__(self, name, ip, account, password):
        self.name = name
        self.ip = ip
        self.account = account
        self.password = password


class Doorbell(Camera):
    def __init__(self, name, ip, account, password, location):
        super().__init__(name, ip, account, password)
        self.location = location

        self.endpoint = f"http://{self.ip}/cgi-bin/snapshot.cgi"
        self.auth = requests.auth.HTTPDigestAuth(account, password)


class CameraSystem:
    def __init__(self, doors: Dict[str, DoorConfig], frigate_cameras: list):
        self.captured_cameras = frigate_cameras
        self.cameras = [
            Doorbell(
                name,
                door_config.ip,
                door_config.account,
                door_config.password,
                door_config.location,
            )
            for name, door_config in doors.items()
        ]
