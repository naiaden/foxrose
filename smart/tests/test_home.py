from tests.conftest import MockGroup, MockRoom, create_test_client, make_mock_home


class TestHomeOverview:
    def test_active_home(self):
        group = MockGroup(on=True)
        room = MockRoom("room1", "Living", groups=[group])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.get("/home")
        assert response.status_code == 200
        assert response.json()["home_active"] is True
        assert response.json()["nr_bridges"] == 1

    def test_inactive_home(self):
        room = MockRoom("room1", "Living", groups=[])
        mock_home = make_mock_home(rooms=[room])
        client = create_test_client(mock_home)

        response = client.get("/home")
        assert response.status_code == 200
        assert response.json()["home_active"] is False


class TestHomeUpdate:
    def test_update_calls_initialise(self):
        mock_home = make_mock_home()
        client = create_test_client(mock_home)

        response = client.post("/home/update")
        assert response.status_code == 200
        mock_home.initialise.assert_called_once()
