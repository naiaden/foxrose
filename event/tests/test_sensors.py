"""Tests for Sensor and SensorSystem classes."""

import time

from sensors import Sensor, SensorType, SensorSystem


class TestSensor:
    """Functional tests for Sensor class."""

    def test_sensor_str_representation(self):
        """Sensor __str__ should include device_id, name, and type."""
        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )

        sensor_str = str(sensor)

        assert "sensor001" in sensor_str
        assert "Living Room" in sensor_str
        assert "INDOOR" in sensor_str

    def test_sensor_from_string(self):
        """Sensor.from_string should parse sensor definition string."""
        sensor = Sensor.from_string("sensor001:Living Room:INDOOR")

        assert sensor.device_id == "sensor001"
        assert sensor.name == "Living Room"
        assert sensor.sensor_type == SensorType.INDOOR

    def test_sensor_from_string_lowercase(self):
        """Sensor.from_string should handle lowercase type."""
        sensor = Sensor.from_string("sensor001:Living Room:indoor")

        assert sensor.sensor_type == SensorType.INDOOR

    def test_sensor_from_string_outdoor(self):
        """Sensor.from_string should parse outdoor sensor."""
        sensor = Sensor.from_string("sensor002:Garden:outdoor")

        assert sensor.sensor_type == SensorType.OUTDOOR


class TestSensorSystem:
    """Functional tests for SensorSystem class."""

    def test_sensor_system_get_sensor(self, sample_sensors):
        """SensorSystem should retrieve existing sensors."""
        system = SensorSystem(state=None, sensors=sample_sensors)

        sensor = system.get_sensor("sensor001")

        assert sensor.device_id == "sensor001"
        assert sensor.name == "Living Room"

    def test_sensor_system_get_sensor_creates_unknown(self, sample_sensors):
        """SensorSystem should create unknown sensor for unknown ID."""
        system = SensorSystem(state=None, sensors=sample_sensors)

        sensor = system.get_sensor("unknown001")

        assert sensor.device_id == "unknown001"
        assert sensor.sensor_type == SensorType.UNKNOWN

    def test_sensor_system_update_presence(self, sample_sensors):
        """SensorSystem should track presence updates."""
        system = SensorSystem(state=None, sensors=sample_sensors)
        sensor = system.get_sensor("sensor001")

        timestamp = time.time()
        system.update_presence(sensor, timestamp)

        assert system.last_updates.get("sensor001") == timestamp

    def test_sensor_system_update_presence_keeps_latest(self, sample_sensors):
        """SensorSystem should keep the latest presence timestamp."""
        system = SensorSystem(state=None, sensors=sample_sensors)
        sensor = system.get_sensor("sensor001")

        system.update_presence(sensor, 100.0)
        system.update_presence(sensor, 200.0)

        assert system.last_updates.get("sensor001") == 200.0

    def test_sensor_system_multiple_sensors(self, sample_sensors):
        """SensorSystem should handle multiple sensors."""
        system = SensorSystem(state=None, sensors=sample_sensors)

        assert len(system.sensors) == 2

    def test_sensor_system_indoor_sensor_type(self, sample_sensors):
        """SensorSystem should correctly identify indoor sensors."""
        system = SensorSystem(state=None, sensors=sample_sensors)

        sensor = system.get_sensor("sensor001")
        assert sensor.sensor_type == SensorType.INDOOR

    def test_sensor_system_outdoor_sensor_type(self, sample_sensors):
        """SensorSystem should correctly identify outdoor sensors."""
        system = SensorSystem(state=None, sensors=sample_sensors)

        sensor = system.get_sensor("sensor002")
        assert sensor.sensor_type == SensorType.OUTDOOR


class TestSensorSystemWindow:
    """Tests for presence event window logic."""

    def test_should_route_event_first_time(self, sample_sensors):
        """First event should always be routed."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First event should be routed
        assert system.should_route_event("sensor001", 100.0) is True

    def test_should_route_event_within_window(self, sample_sensors):
        """Event within window should not be routed."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First event
        system.mark_event_routed("sensor001", 100.0)

        # Event 100 seconds later (within 300s window) should not be routed
        assert system.should_route_event("sensor001", 200.0) is False

    def test_should_route_event_after_window(self, sample_sensors):
        """Event after window should be routed."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First event
        system.mark_event_routed("sensor001", 100.0)

        # Event 400 seconds later (after 300s window) should be routed
        assert system.should_route_event("sensor001", 500.0) is True

    def test_should_route_event_different_sensors(self, sample_sensors):
        """Events for different sensors should be independent."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First sensor event
        system.mark_event_routed("sensor001", 100.0)

        # Second sensor should still be routed
        assert system.should_route_event("sensor002", 150.0) is True

    def test_should_route_event_custom_window(self, sample_sensors):
        """Custom window timeout should be respected."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=60)

        # First event
        system.mark_event_routed("sensor001", 100.0)

        # Event 30 seconds later (within 60s window) should not be routed
        assert system.should_route_event("sensor001", 130.0) is False

        # Event 60 seconds later (at window boundary) should be routed
        assert system.should_route_event("sensor001", 160.0) is True

    def test_mark_event_routed_updates_timestamp(self, sample_sensors):
        """mark_event_routed should update the last_routed_events dict."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        system.mark_event_routed("sensor001", 100.0)
        assert system.last_routed_events.get("sensor001") == 100.0

        system.mark_event_routed("sensor001", 500.0)
        assert system.last_routed_events.get("sensor001") == 500.0

    def test_is_new_window_first_time(self, sample_sensors):
        """is_new_window should return False for first event (no previous window)."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First event should not be considered a "new window"
        assert system.is_new_window("sensor001", 100.0) is False

    def test_is_new_window_within_window(self, sample_sensors):
        """is_new_window should return False within the window."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First event
        system.mark_event_routed("sensor001", 100.0)

        # Event 100 seconds later (within 300s window) should not be a new window
        assert system.is_new_window("sensor001", 200.0) is False

    def test_is_new_window_after_window(self, sample_sensors):
        """is_new_window should return True after window expiration."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First event
        system.mark_event_routed("sensor001", 100.0)

        # Event 400 seconds later (after 300s window) should be a new window
        assert system.is_new_window("sensor001", 500.0) is True

    def test_is_new_window_different_sensors(self, sample_sensors):
        """is_new_window should be False for sensors with no previous events."""
        system = SensorSystem(state=None, sensors=sample_sensors, window_timeout=300)

        # First sensor event
        system.mark_event_routed("sensor001", 100.0)

        # Second sensor should not be a new window (no previous window)
        assert system.is_new_window("sensor002", 150.0) is False
