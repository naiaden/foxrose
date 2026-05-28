import requests
import os

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

        self.endpoint = f'http://{self.ip}/cgi-bin/snapshot.cgi'
        self.auth = requests.auth.HTTPDigestAuth(account, password)

class CameraSystem:
    def __init__(self):
        self.captured_cameras = os.environ['FRIGATE_CAMERAS'].split(',')
        self.cameras = [
            # Camera("tuinhuis", )
            Doorbell("achterdeur", os.environ['ACHTERDEUR_IP'], os.environ['ACHTERDEUR_ACCOUNT'], os.environ['ACHTERDEUR_PASSWORD'], "9901"),
            Doorbell("voordeur", os.environ['VOORDEUR_IP'], os.environ['VOORDEUR_ACCOUNT'], os.environ['VOORDEUR_PASSWORD'], "9903"),
        ]

