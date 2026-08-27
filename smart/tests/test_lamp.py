from tests.conftest import MockLamp, create_test_client, make_mock_home


class TestLampInfo:
    def test_lamp_found(self):
        lamp = MockLamp("lamp1", on=True, brightness=50)
        mock_home = make_mock_home(lamps=[lamp])
        client = create_test_client(mock_home)

        response = client.get("/lamp/lamp1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Lamp lamp1"
        assert data["on"] is True
        assert data["brightness"] == 50

    def test_lamp_not_found(self):
        mock_home = make_mock_home(lamps=[])
        client = create_test_client(mock_home)

        response = client.get("/lamp/unknown")
        assert response.status_code == 404


class TestLampActive:
    def test_lamp_active_on(self):
        lamp = MockLamp("lamp1", on=False)
        mock_home = make_mock_home(lamps=[lamp])
        client = create_test_client(mock_home)

        response = client.post("/lamp/lamp1/active/on")
        assert response.status_code == 200
        assert lamp.on is True

    def test_lamp_active_off(self):
        lamp = MockLamp("lamp1", on=True)
        mock_home = make_mock_home(lamps=[lamp])
        client = create_test_client(mock_home)

        response = client.post("/lamp/lamp1/active/off")
        assert response.status_code == 200
        assert lamp.on is False


class TestLampBrightness:
    def test_brightness_increase(self):
        lamp = MockLamp("lamp1", on=False, brightness=50)
        mock_home = make_mock_home(lamps=[lamp])
        client = create_test_client(mock_home)

        response = client.post("/lamp/lamp1/brightness/10")
        assert response.status_code == 200
        assert lamp.brightness == 60
        assert lamp.on is True

    def test_brightness_overflow(self):
        lamp = MockLamp("lamp1", on=False, brightness=95)
        mock_home = make_mock_home(lamps=[lamp])
        client = create_test_client(mock_home)

        response = client.post("/lamp/lamp1/brightness/10")
        assert response.status_code == 200
        assert lamp.brightness == 100

    def test_brightness_underflow(self):
        lamp = MockLamp("lamp1", on=False, brightness=5)
        mock_home = make_mock_home(lamps=[lamp])
        client = create_test_client(mock_home)

        response = client.post("/lamp/lamp1/brightness/-10")
        assert response.status_code == 200
        assert lamp.brightness == 0
