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
