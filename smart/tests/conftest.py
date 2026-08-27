from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config import SmartConfig
from src.routers import home as home_router
from src.routers import lamp as lamp_router
from src.routers import room as room_router


class MockGroup:
    def __init__(self, group_id=None, on=False, brightness=0):
        self.id = group_id or "group-1"
        self._on = on
        self._brightness = brightness

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        self._on = value

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = max(0, min(value, 100))


class MockScene:
    def __init__(self, name):
        self.name = name
        self.activated = False

    def activate(self):
        self.activated = True


class MockLamp:
    def __init__(self, lamp_id, on=False, brightness=0):
        self.id = lamp_id
        self.name = f"Lamp {lamp_id}"
        self._on = on
        self._brightness = brightness
        self._colour = ("mirek", 200)

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, value):
        self._on = value

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = max(0, min(value, 100))
        self._on = True

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, value):
        self._colour = value

    def summary(self):
        return {
            "name": self.name,
            "id": self.id,
            "on": self._on,
            "brightness": self._brightness,
            "colour": self._colour,
        }


class MockRoom:
    def __init__(self, room_id, name, groups=None, scenes=None):
        self.id = room_id
        self.name = name
        self.groups = groups or []
        self.scenes = scenes or []

    def summary(self):
        return {
            "name": self.name,
            "id": self.id,
            "nr_lamps": 0,
            "lamps": [],
            "nr_scenes": len(self.scenes),
            "scenes": [str(s) for s in self.scenes],
            "nr_groups": len(self.groups),
            "groups": [str(g) for g in self.groups],
        }


def make_mock_home(
    rooms=None,
    lamps=None,
    hues=None,
):
    hues = hues or [MagicMock()]
    lamps = lamps or []
    rooms = rooms or []

    mock_home = MagicMock()
    mock_home.hues = hues
    mock_home.rooms = rooms
    mock_home.lamps = lamps
    mock_home.initialise = MagicMock()

    def get_room_with_id(room_id):
        for room in rooms:
            if room.id == room_id:
                return room
        return None

    def get_lamp_with_id(lamp_id):
        for lamp in lamps:
            if lamp.id == lamp_id:
                return lamp
        return None

    mock_home.get_room_with_id.side_effect = get_room_with_id
    mock_home.get_lamp_with_id.side_effect = get_lamp_with_id
    return mock_home


def create_test_client(mock_home, config=None):
    if config is None:
        config = SmartConfig()

    # Reset any module-level state before each test so tests are fully isolated.
    room_router.reset_scene_state()

    test_app = FastAPI()
    test_app.include_router(home_router.router, prefix="", tags=["home"])
    test_app.include_router(room_router.router, prefix="", tags=["room"])
    test_app.include_router(lamp_router.router, prefix="", tags=["lamp"])

    @test_app.get("/")
    async def root():
        return {"message": "Hello World"}

    home_router.set_home(mock_home)
    home_router.set_config(config)
    room_router.set_home(mock_home)
    lamp_router.set_home(mock_home)

    return TestClient(test_app)
