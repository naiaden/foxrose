"""Tests for system events and system monitor."""

from unittest.mock import Mock
import json

from routing.router import NotificationRouter
from routing.event_handlers import SystemEventHandler
from events.system_event import (
    SystemEvent,
    HighCPUEvent,
    HighSwapUsageEvent,
    HighTmpUsageEvent,
)


class TestSystemEvents:
    """Functional tests for system events."""

    def test_high_cpu_event_creation(self):
        """HighCPUEvent should be created with correct attributes."""
        event = HighCPUEvent(hostname="testhost", cpu_percentage=85.5, threshold=80.0)

        assert event.hostname == "testhost"
        assert event.cpu_percentage == 85.5
        assert event.threshold == 80.0
        assert isinstance(event, SystemEvent)

    def test_high_swap_event_creation(self):
        """HighSwapUsageEvent should be created with correct attributes."""
        event = HighSwapUsageEvent(
            hostname="testhost", swap_percentage=92.3, threshold=90.0
        )

        assert event.hostname == "testhost"
        assert event.swap_percentage == 92.3
        assert event.threshold == 90.0
        assert isinstance(event, SystemEvent)

    def test_high_tmp_event_creation(self):
        """HighTmpUsageEvent should be created with correct attributes."""
        event = HighTmpUsageEvent(
            hostname="testhost", tmp_percentage=95.0, threshold=90.0, path="/tmp"
        )

        assert event.hostname == "testhost"
        assert event.tmp_percentage == 95.0
        assert event.threshold == 90.0
        assert event.path == "/tmp"
        assert isinstance(event, SystemEvent)

    def test_high_cpu_event_string_representation(self):
        """HighCPUEvent should have correct string representation."""
        event = HighCPUEvent(hostname="testhost", cpu_percentage=85.5, threshold=80.0)
        event_str = str(event)

        assert "HighCPUEvent" in event_str
        assert "testhost" in event_str
        assert "85.5%" in event_str
        assert "80.0%" in event_str

    def test_high_swap_event_string_representation(self):
        """HighSwapUsageEvent should have correct string representation."""
        event = HighSwapUsageEvent(
            hostname="testhost", swap_percentage=92.3, threshold=90.0
        )
        event_str = str(event)

        assert "HighSwapUsageEvent" in event_str
        assert "testhost" in event_str
        assert "92.3%" in event_str
        assert "90.0%" in event_str

    def test_high_tmp_event_string_representation(self):
        """HighTmpUsageEvent should have correct string representation."""
        event = HighTmpUsageEvent(
            hostname="testhost", tmp_percentage=95.0, threshold=90.0, path="/tmp"
        )
        event_str = str(event)

        assert "HighTmpUsageEvent" in event_str
        assert "testhost" in event_str
        assert "95.0%" in event_str
        assert "/tmp" in event_str


class TestSystemEventHandler:
    """Functional tests for SystemEventHandler."""

    def test_system_event_handler_subscribes_to_system_events(
        self, mock_state_manager, mock_sink
    ):
        """SystemEventHandler should subscribe to SystemEvent."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        SystemEventHandler(router, mock_state_manager)

        assert SystemEvent in router._subscribers

    def test_system_event_handler_routes_high_cpu(self, mock_state_manager, mock_sink):
        """SystemEventHandler should handle HighCPUEvent."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SystemEventHandler(router, mock_state_manager)

        event = HighCPUEvent(hostname="testhost", cpu_percentage=85.0, threshold=80.0)
        handler.handle_system_event(event)

        # Event should be routed to sinks
        mock_sink.send.assert_called_once()

    def test_system_event_handler_routes_high_swap(self, mock_state_manager, mock_sink):
        """SystemEventHandler should handle HighSwapUsageEvent."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SystemEventHandler(router, mock_state_manager)

        event = HighSwapUsageEvent(
            hostname="testhost", swap_percentage=92.0, threshold=90.0
        )
        handler.handle_system_event(event)

        # Event should be routed to sinks
        mock_sink.send.assert_called_once()

    def test_system_event_handler_routes_high_tmp(self, mock_state_manager, mock_sink):
        """SystemEventHandler should handle HighTmpUsageEvent."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SystemEventHandler(router, mock_state_manager)

        event = HighTmpUsageEvent(
            hostname="testhost", tmp_percentage=95.0, threshold=90.0, path="/tmp"
        )
        handler.handle_system_event(event)

        # Event should be routed to sinks
        mock_sink.send.assert_called_once()


class TestMQTTSystemEventHandling:
    """Functional tests for MQTT system event handling."""

    def test_mqtt_handles_cpu_event(self):
        """MQTTMainDispatcher should handle CPU system events."""
        from handlers.mqtt import MQTTMainDispatcher

        mock_router = Mock()
        mock_state = Mock()
        dispatcher = MQTTMainDispatcher(mock_state, mock_router, "localhost")

        # Simulate MQTT message
        payload_data = {
            "hostname": "testhost",
            "cpu_percentage": 85.5,
            "threshold": 80.0,
        }
        payload = json.dumps(payload_data).encode()

        mock_message = Mock()
        mock_message.topic = "foxrosehip/system/testhost/cpu"
        mock_message.payload = payload

        dispatcher._handle_system_event(mock_message)

        # Should have routed a HighCPUEvent
        mock_router.route_event.assert_called_once()
        event = mock_router.route_event.call_args[0][0]
        assert isinstance(event, HighCPUEvent)
        assert event.hostname == "testhost"
        assert event.cpu_percentage == 85.5
        assert event.threshold == 80.0

    def test_mqtt_handles_swap_event(self):
        """MQTTMainDispatcher should handle swap system events."""
        from handlers.mqtt import MQTTMainDispatcher

        mock_router = Mock()
        mock_state = Mock()
        dispatcher = MQTTMainDispatcher(mock_state, mock_router, "localhost")

        # Simulate MQTT message
        payload_data = {
            "hostname": "testhost",
            "swap_percentage": 92.3,
            "threshold": 90.0,
        }
        payload = json.dumps(payload_data).encode()

        mock_message = Mock()
        mock_message.topic = "foxrosehip/system/testhost/swap"
        mock_message.payload = payload

        dispatcher._handle_system_event(mock_message)

        # Should have routed a HighSwapUsageEvent
        mock_router.route_event.assert_called_once()
        event = mock_router.route_event.call_args[0][0]
        assert isinstance(event, HighSwapUsageEvent)
        assert event.hostname == "testhost"
        assert event.swap_percentage == 92.3
        assert event.threshold == 90.0

    def test_mqtt_handles_tmp_event(self):
        """MQTTMainDispatcher should handle tmp system events."""
        from handlers.mqtt import MQTTMainDispatcher

        mock_router = Mock()
        mock_state = Mock()
        dispatcher = MQTTMainDispatcher(mock_state, mock_router, "localhost")

        # Simulate MQTT message
        payload_data = {
            "hostname": "testhost",
            "tmp_percentage": 95.0,
            "threshold": 90.0,
            "path": "/tmp",
        }
        payload = json.dumps(payload_data).encode()

        mock_message = Mock()
        mock_message.topic = "foxrosehip/system/testhost/tmp"
        mock_message.payload = payload

        dispatcher._handle_system_event(mock_message)

        # Should have routed a HighTmpUsageEvent
        mock_router.route_event.assert_called_once()
        event = mock_router.route_event.call_args[0][0]
        assert isinstance(event, HighTmpUsageEvent)
        assert event.hostname == "testhost"
        assert event.tmp_percentage == 95.0
        assert event.threshold == 90.0
        assert event.path == "/tmp"

    def test_mqtt_handles_unknown_system_event(self):
        """MQTTMainDispatcher should handle unknown system event types gracefully."""
        from handlers.mqtt import MQTTMainDispatcher

        mock_router = Mock()
        mock_state = Mock()
        dispatcher = MQTTMainDispatcher(mock_state, mock_router, "localhost")

        # Simulate MQTT message with unknown event type
        payload_data = {"hostname": "testhost", "some_value": 123}
        payload = json.dumps(payload_data).encode()

        mock_message = Mock()
        mock_message.topic = "foxrosehip/system/testhost/unknown"
        mock_message.payload = payload

        # Should not raise an exception
        dispatcher._handle_system_event(mock_message)

        # Should not have routed any event
        mock_router.route_event.assert_not_called()
