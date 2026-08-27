"""Tests for DeviceEvent and its subclasses."""

import pytest

from events.device_event import (
    DeviceEvent,
    BatteryEvent,
    LowBatteryEvent,
    TemperatureEvent,
)
from events.event import Event


class TestDeviceEvent:
    """Functional tests for DeviceEvent."""

    def test_device_event_inherits_from_event(self):
        """DeviceEvent should be a subclass of Event."""
        event = DeviceEvent()
        assert isinstance(event, Event)

    def test_device_event_str_representation(self):
        """DeviceEvent __str__ should include 'DeviceEvent'."""
        event = DeviceEvent()
        event_str = str(event)

        assert "DeviceEvent" in event_str


class TestBatteryEvent:
    """Functional tests for BatteryEvent."""

    def test_battery_event_has_device_and_percentage(self):
        """BatteryEvent should store device name and battery percentage."""
        event = BatteryEvent(device="sensor001", percentage=75)

        assert event.device == "sensor001"
        assert event.percentage == 75

    def test_battery_event_str_includes_details(self):
        """BatteryEvent __str__ should include device and percentage."""
        event = BatteryEvent(device="sensor001", percentage=75)
        event_str = str(event)

        assert "sensor001" in event_str
        assert "75" in event_str
        assert "BatteryEvent" in event_str

    def test_battery_event_is_frozen(self):
        """BatteryEvent should be immutable."""
        event = BatteryEvent(device="sensor001", percentage=75)

        with pytest.raises(AttributeError):
            event.percentage = 50


class TestLowBatteryEvent:
    """Functional tests for LowBatteryEvent."""

    def test_low_battery_event_inherits_from_battery_event(self):
        """LowBatteryEvent should be a subclass of BatteryEvent."""
        event = LowBatteryEvent(device="sensor001", percentage=5)

        assert isinstance(event, BatteryEvent)
        assert isinstance(event, DeviceEvent)
        assert isinstance(event, Event)

    def test_low_battery_event_str_representation(self):
        """LowBatteryEvent __str__ should indicate low battery status."""
        event = LowBatteryEvent(device="sensor001", percentage=5)
        event_str = str(event)

        assert "LowBatteryEvent" in event_str
        assert "sensor001" in event_str

    def test_low_battery_event_for_low_percentage(self):
        """LowBatteryEvent should be used for low battery conditions."""
        # This is a functional test - LowBatteryEvent is for low battery scenarios
        event = LowBatteryEvent(device="sensor001", percentage=3)

        assert event.percentage < 10  # Low battery threshold


class TestTemperatureEvent:
    """Functional tests for TemperatureEvent."""

    def test_temperature_event_has_device_and_temperature(self):
        """TemperatureEvent should store device and temperature value."""
        event = TemperatureEvent(device="therm001", temperature=22.5)

        assert event.device == "therm001"
        assert event.temperature == 22.5

    def test_temperature_event_str_includes_details(self):
        """TemperatureEvent __str__ should include device and temperature."""
        event = TemperatureEvent(device="therm001", temperature=22.5)
        event_str = str(event)

        assert "therm001" in event_str
        assert "22.5" in event_str
        assert "TemperatureEvent" in event_str

    def test_temperature_event_handles_negative_temperatures(self):
        """TemperatureEvent should handle negative temperatures (e.g., outdoors)."""
        event = TemperatureEvent(device="outdoor_therm", temperature=-5.0)

        assert event.temperature == -5.0

    def test_temperature_event_handles_high_temperatures(self):
        """TemperatureEvent should handle high temperatures."""
        event = TemperatureEvent(device="indoor_therm", temperature=30.0)

        assert event.temperature == 30.0
