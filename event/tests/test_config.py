"""Tests for configuration loading."""

import tempfile
import yaml

from config import load_config


class TestConfigLoader:
    """Tests for YAML configuration loading."""

    def test_load_config_basic(self):
        """Should load a valid config file."""
        config_data = {
            "mqtt": {"main_server": "192.168.1.1", "frigate_server": "192.168.1.2"},
            "servers": {"frigate_server": "192.168.1.2"},
            "doors": {},
            "notification": {"doorbell_topic": "test_topic", "bot_name": "test_bot"},
            "users": [],
            "valid_doorcards": [],
            "frigate_cameras": ["camera1"],
            "thermometers": {},
            "sensors": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = load_config(f.name)

            assert config.mqtt.main_server == "192.168.1.1"
            assert config.mqtt.frigate_server == "192.168.1.2"
            assert config.frigate_cameras == ["camera1"]

    def test_load_config_with_users(self):
        """Should parse users correctly."""
        config_data = {
            "mqtt": {"main_server": "192.168.1.1", "frigate_server": "192.168.1.2"},
            "servers": {"frigate_server": "192.168.1.2"},
            "doors": {},
            "notification": {"doorbell_topic": "test_topic", "bot_name": "test_bot"},
            "users": [
                {
                    "name": "alice",
                    "telegram_id": 123456,
                    "keycards": ["card1", "card2"],
                },
                {"name": "bob", "telegram_id": 789012, "keycards": []},
            ],
            "valid_doorcards": ["card1", "card2"],
            "frigate_cameras": [],
            "thermometers": {},
            "sensors": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = load_config(f.name)

            assert len(config.users) == 2
            assert config.users[0].name == "alice"
            assert config.users[0].telegram_user_id == 123456
            assert "card1" in config.users[0].keycards
            assert config.users[1].name == "bob"

    def test_load_config_with_sensors(self):
        """Should parse sensors correctly."""
        config_data = {
            "mqtt": {"main_server": "192.168.1.1", "frigate_server": "192.168.1.2"},
            "servers": {"frigate_server": "192.168.1.2"},
            "doors": {},
            "notification": {"doorbell_topic": "test_topic", "bot_name": "test_bot"},
            "users": [],
            "valid_doorcards": [],
            "frigate_cameras": [],
            "thermometers": {},
            "sensors": [
                {"device_id": "001", "name": "front_door", "type": "OUTDOOR"},
                {"device_id": "002", "name": "living_room", "type": "INDOOR"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = load_config(f.name)

            assert len(config.sensors) == 2
            assert config.sensors[0].device_id == "001"
            assert config.sensors[0].sensor_type.name == "OUTDOOR"
            assert config.sensors[1].sensor_type.name == "INDOOR"
