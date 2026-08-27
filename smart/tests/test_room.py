from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routers import room as room_router
from tests.conftest import (
    MockGroup,
    MockRoom,
    MockScene,
    create_test_client,
    make_mock_home,
)


class TestRoomList:
    def test_room_list_returns_all_rooms(self):
        room1 = MockRoom("room1", "Living", groups=[], scenes=[])
        room2 = MockRoom("room2", "Kitchen", groups=[], scenes=[])
        mock_home = make_mock_home(rooms=[room1, room2])
        client = create_test_client(mock_home)

        response = client.get("/room")
        assert response.status_code == 200
        assert response.json() == [["Living", "room1"], ["Kitchen", "room2"]]

    def test_room_list_empty_home(self):
        mock_home = make_mock_home(rooms=[])
        client = create_test_client(mock_home)

        response = client.get("/room")
        assert response.status_code == 200
        assert response.json() == []


class TestRoomScenes:
    def test_room_scenes_found(self):
        scene1 = MockScene("Scene 1")
        scene2 = MockScene("Scene 2")
        room = MockRoom("room1", "Living", groups=[], scenes=[scene1, scene2])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.get("/room/room1/scenes")
        assert response.status_code == 200
        assert response.json() == ["Scene 1", "Scene 2"]

    def test_room_scenes_not_found(self):
        mock_home = make_mock_home(rooms=[])
        client = create_test_client(mock_home)

        response = client.get("/room/unknown/scenes")
        assert response.status_code == 404


class TestRoomInfo:
    def test_room_found(self):
        room = MockRoom("room1", "Living", groups=[], scenes=[])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.get("/room/room1")
        assert response.status_code == 200
        assert response.json()["name"] == "Living"
        assert response.json()["id"] == "room1"

    def test_room_not_found(self):
        mock_home = make_mock_home(rooms=[])
        client = create_test_client(mock_home)

        response = client.get("/room/unknown")
        assert response.status_code == 404


class TestRoomActive:
    def test_room_active_on(self):
        group = MockGroup(on=False)
        room = MockRoom("room1", "Living", groups=[group])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.post("/room/room1/active/on")
        assert response.status_code == 200
        assert group.on is True

    def test_room_active_off(self):
        group = MockGroup(on=True)
        room = MockRoom("room1", "Living", groups=[group])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.post("/room/room1/active/off")
        assert response.status_code == 200
        assert group.on is False


class TestRoomNight:
    def test_room_night_found(self):
        night_scene = MockScene("Nightlight")
        room = MockRoom("room1", "Living", scenes=[night_scene])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.post("/room/room1/night")
        assert response.status_code == 200
        assert night_scene.activated is True

    def test_room_night_not_found(self):
        mock_home = make_mock_home(rooms=[])
        client = create_test_client(mock_home)

        response = client.post("/room/unknown/night")
        assert response.status_code == 404


class TestRoomSceneNext:
    def test_scene_not_found(self):
        mock_home = make_mock_home(rooms=[])
        client = create_test_client(mock_home)

        response = client.post("/room/unknown/scene/next")
        assert response.status_code == 404

    def test_rotation_advances_through_scenes(self):
        scene1 = MockScene("Scene 1")
        scene2 = MockScene("Scene 2")
        scene3 = MockScene("Scene 3")
        room = MockRoom("room1", "Living", scenes=[scene1, scene2, scene3])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        # First pass: each scene should be activated exactly once, in order.
        client.post("/room/room1/scene/next")
        assert scene1.activated is True
        assert scene2.activated is False
        assert scene3.activated is False

        client.post("/room/room1/scene/next")
        assert scene1.activated is True
        assert scene2.activated is True
        assert scene3.activated is False

        client.post("/room/room1/scene/next")
        assert scene1.activated is True
        assert scene2.activated is True
        assert scene3.activated is True

    def test_rotation_wraps_around(self):
        scene1 = MockScene("Scene 1")
        scene2 = MockScene("Scene 2")
        room = MockRoom("room1", "Living", scenes=[scene1, scene2])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        # Cycle through both scenes twice; rotation should not break after a full lap.
        for _ in range(4):
            response = client.post("/room/room1/scene/next")
            assert response.status_code == 200

        assert scene1.activated is True
        assert scene2.activated is True

    def test_isolated_counters_per_room(self):
        scene_a1 = MockScene("A1")
        scene_a2 = MockScene("A2")
        scene_b1 = MockScene("B1")
        room_a = MockRoom("room-a", "Room A", scenes=[scene_a1, scene_a2])
        room_b = MockRoom("room-b", "Room B", scenes=[scene_b1])
        mock_home = make_mock_home(rooms=[room_a, room_b])
        client = create_test_client(mock_home)

        client.post("/room/room-a/scene/next")  # room-a -> scene A1
        client.post("/room/room-b/scene/next")  # room-b -> scene B1

        assert scene_a1.activated is True
        assert scene_a2.activated is False
        assert scene_b1.activated is True

        client.post("/room/room-a/scene/next")  # room-a -> scene A2
        assert scene_a2.activated is True


class TestRoomIdDropdown:
    """When routes are registered *after* `set_home()`, the `room_id` path
    parameter becomes an Enum of available rooms (rendering a dropdown in the
    docs page). Invalid room ids are then rejected by validation (422)."""

    def test_room_id_is_enum_when_registered_after_set_home(self):
        room = MockRoom("room1", "Living")
        mock_home = make_mock_home(rooms=[room])

        # set_home before include_router -> RoomId resolves to the room Enum
        room_router.set_home(mock_home)

        test_app = FastAPI()
        test_app.include_router(room_router.router, tags=["room"])
        client = TestClient(test_app)

        # Unknown room id -> enum validation failure (422), not the 404 path
        assert client.get("/room/unknown").status_code == 422
        # Known room id -> works
        assert client.get("/room/room1").status_code == 200

    def test_room_id_falls_back_to_str_without_rooms(self):
        mock_home = make_mock_home(rooms=[])

        room_router.set_home(mock_home)

        test_app = FastAPI()
        test_app.include_router(room_router.router, tags=["room"])
        client = TestClient(test_app)

        # No rooms -> no enum -> any id yields the regular 404 path
        assert client.get("/room/unknown").status_code == 404
