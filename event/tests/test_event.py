"""Tests for the base Event class."""

import time
import pytest

from events.event import Event, color_wrap


class TestEvent:
    """Functional tests for the Event base class."""

    def test_event_has_create_time(self):
        """Event should automatically record creation time."""
        before = time.time()
        event = Event()
        after = time.time()

        assert before <= event._create_time <= after

    def test_event_create_time_str_format(self):
        """Event create_time_str should return a human-readable timestamp."""
        event = Event()
        time_str = event.create_time_str

        # Should be a non-empty string
        assert isinstance(time_str, str)
        assert len(time_str) > 0

    def test_event_str_representation(self):
        """Event __str__ should include timestamp and event type."""
        event = Event()
        event_str = str(event)

        assert "Event" in event_str
        assert event.create_time_str in event_str

    def test_event_is_frozen(self):
        """Event should be immutable (frozen dataclass)."""
        event = Event()

        with pytest.raises(AttributeError):
            event._create_time = 12345

    def test_color_wrap_decorator_adds_colors(self):
        """color_wrap decorator should wrap output with color codes."""
        event = Event()

        @color_wrap
        def sample_method(self):
            return "test message"

        result = sample_method(event)

        # Should contain the original message
        assert "test message" in result
        # Should contain color codes (the _SS and _SE attributes)
        assert event._SS in result
        assert event._SE in result

    def test_color_wrap_preserves_function_name(self):
        """color_wrap should preserve the original function's metadata."""

        @color_wrap
        def my_method(self):
            return "result"

        # The wrapper should preserve the name
        assert my_method.__name__ == "my_method"
