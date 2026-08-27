"""Tests for TemperatureTracker and TemperatureSystem classes."""

import time

from temperatures import TemperatureTrend, TemperatureTracker, TemperatureSystem


class TestTemperatureTrend:
    """Functional tests for TemperatureTrend enum."""

    def test_trend_as_emoji(self):
        """TemperatureTrend should return correct emoji for each trend."""
        assert TemperatureTrend.RISING.as_emoji() == "🔴"
        assert TemperatureTrend.FALLING.as_emoji() == "🔵"
        assert TemperatureTrend.STABLE.as_emoji() == "⚪"


class TestTemperatureTracker:
    """Functional tests for TemperatureTracker class."""

    def test_tracker_initial_state(self):
        """TemperatureTracker should start with empty history."""
        tracker = TemperatureTracker(device="therm001", name="Living Room")

        assert len(tracker.history) == 0
        assert tracker.reading == TemperatureTrend.STABLE

    def test_tracker_add_first_reading(self):
        """TemperatureTracker should accept first reading."""
        tracker = TemperatureTracker(device="therm001", name="Living Room")
        now = time.time()

        result = tracker.add_reading(22.0, now)

        assert result == TemperatureTrend.STABLE
        assert len(tracker.history) == 1

    def test_tracker_detects_rising_trend(self):
        """TemperatureTracker should detect rising temperature trend."""
        tracker = TemperatureTracker(device="therm001", name="Living Room")
        now = time.time()

        # Add initial reading
        tracker.add_reading(20.0, now)
        # Add higher reading after a small delay
        tracker.add_reading(22.0, now + 60)

        assert tracker.reading == TemperatureTrend.RISING

    def test_tracker_detects_falling_trend(self):
        """TemperatureTracker should detect falling temperature trend."""
        tracker = TemperatureTracker(device="therm001", name="Living Room")
        now = time.time()

        # Add initial reading
        tracker.add_reading(22.0, now)
        # Add lower reading after a small delay
        tracker.add_reading(20.0, now + 60)

        assert tracker.reading == TemperatureTrend.FALLING

    def test_tracker_stable_within_buffer(self):
        """TemperatureTracker should be stable when within buffer range."""
        tracker = TemperatureTracker(device="therm001", name="Living Room", buffer=0.5)
        now = time.time()

        # Add initial reading
        tracker.add_reading(22.0, now)
        # Add reading within buffer
        tracker.add_reading(22.3, now + 60)

        assert tracker.reading == TemperatureTrend.STABLE

    def test_tracker_ignores_large_jumps(self):
        """TemperatureTracker should ignore readings with large jumps."""
        tracker = TemperatureTracker(
            device="therm001", name="Living Room", max_allowed_jump=2.0
        )
        now = time.time()

        # Add initial reading
        tracker.add_reading(22.0, now)
        # Add reading with large jump (should be ignored)
        result = tracker.add_reading(30.0, now + 60)

        assert result == TemperatureTrend.STABLE
        # History should still only have 1 entry (the ignored one wasn't added)
        assert len(tracker.history) == 1

    def test_tracker_prunes_old_readings(self):
        """TemperatureTracker should prune readings outside window."""
        tracker = TemperatureTracker(
            device="therm001", name="Living Room", windows_minutes=5
        )
        now = time.time()

        # Add old reading
        tracker.add_reading(20.0, now - 600)  # 10 minutes ago
        # Add current reading
        tracker.add_reading(22.0, now)

        # Old reading should be pruned
        assert len(tracker.history) == 1

    def test_tracker_calculates_average(self):
        """TemperatureTracker should calculate running average (from first reading in window)."""
        tracker = TemperatureTracker(device="therm001", name="Living Room")
        now = time.time()

        # First reading: returns STABLE, doesn't set current_avg
        tracker.add_reading(20.0, now)
        # Second reading: calculates average from first reading
        tracker.add_reading(22.0, now + 60)

        # current_avg is calculated from history before adding new reading
        # So it's the average of just the first reading: 20.0
        assert tracker.current_avg == 20.0


class TestTemperatureSystem:
    """Functional tests for TemperatureSystem class."""

    def test_temperature_system_get_tracker(self):
        """TemperatureSystem should return tracker for device."""
        system = TemperatureSystem(state=None, thermometers={"therm001": "Living Room"})

        tracker = system.get_tracker("therm001")

        assert tracker.device == "therm001"

    def test_temperature_system_creates_tracker_on_demand(self):
        """TemperatureSystem should create tracker for unknown device."""
        system = TemperatureSystem(state=None, thermometers={})

        tracker = system.get_tracker("unknown_therm")

        assert tracker.device == "unknown_therm"

    def test_temperature_system_add_reading(self):
        """TemperatureSystem should add readings to tracker."""
        system = TemperatureSystem(state=None, thermometers={"therm001": "Living Room"})
        now = time.time()

        result = system.add_reading("therm001", 22.0, now)

        assert result == TemperatureTrend.STABLE

    def test_temperature_system_get_latest_readings(self):
        """TemperatureSystem should return latest readings from all trackers."""
        system = TemperatureSystem(state=None, thermometers={"therm001": "Living Room"})
        now = time.time()

        system.add_reading("therm001", 22.0, now)

        readings = system.get_latest_readings()

        assert len(readings) == 1
        assert readings[0][0] == "Living Room"  # name
        assert readings[0][1][1] == 22.0  # (timestamp, temp) tuple

    def test_temperature_system_multiple_thermometers(self):
        """TemperatureSystem should handle multiple thermometers."""
        system = TemperatureSystem(
            state=None, thermometers={"therm001": "Living Room", "therm002": "Bedroom"}
        )
        now = time.time()

        system.add_reading("therm001", 22.0, now)
        system.add_reading("therm002", 20.0, now)

        readings = system.get_latest_readings()

        assert len(readings) == 2
