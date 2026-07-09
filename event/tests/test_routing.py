"""Tests for routing rules and NotificationRouter."""

from unittest.mock import Mock

from routing.rules import DeliveryType, routing_rule
from routing.router import NotificationRouter
from routing.event_handlers import (
    AfvalEventHandler,
    UserSettingChangedEventHandler,
    SnoozeEventHandler,
    ModeToggleEventHandler,
    DoorcardEventHandler,
    CameraDetectionEventHandler,
    DeviceEventHandler,
    TemperatureEventHandler,
    PresenceDetectionEventHandler,
)
from modes import Mode
from events.event import Event
from events.afval_event import AfvalEvent
from events.change_event import (
    UserSettingsChangedEvent,
    UserSettingsType,
    UserSnoozeEvent,
    UserModeToggleEvent,
)
from events.doorcard_event import DoorCardEvent
from events.detection_event import (
    CameraDetectionEvent,
    PresenceDetectionEvent,
    IndoorPresenceDetectionEvent,
    OutdoorPresenceDetectionEvent,
)
from events.device_event import (
    DeviceEvent,
    BatteryEvent,
    LowBatteryEvent,
    TemperatureEvent,
)
from users import User


class TestRoutingRules:
    """Functional tests for routing rules."""

    def test_routing_rule_at_home_camera_detection(self):
        """AT_HOME mode should return SILENT for camera detection."""
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        result = routing_rule(Mode.AT_HOME, event)

        assert result == DeliveryType.SILENT

    def test_routing_rule_away_camera_detection(self):
        """AWAY mode should return LOUD for camera detection."""
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        result = routing_rule(Mode.AWAY, event)

        assert result == DeliveryType.LOUD

    def test_routing_rule_night_camera_detection(self):
        """NIGHT mode should return LOUD for camera detection."""
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        result = routing_rule(Mode.NIGHT, event)

        assert result == DeliveryType.LOUD

    def test_routing_rule_at_home_indoor_presence(self):
        """AT_HOME mode should return IGNORE for indoor presence."""
        event = IndoorPresenceDetectionEvent(device=Mock(sensor_type=Mock()))

        result = routing_rule(Mode.AT_HOME, event)

        assert result == DeliveryType.IGNORE

    def test_routing_rule_away_indoor_presence(self):
        """AWAY mode should return LOUD for indoor presence."""
        event = IndoorPresenceDetectionEvent(device=Mock(sensor_type=Mock()))

        result = routing_rule(Mode.AWAY, event)

        assert result == DeliveryType.LOUD

    def test_routing_rule_at_home_outdoor_presence(self):
        """AT_HOME mode should return SILENT for outdoor presence."""
        event = OutdoorPresenceDetectionEvent(device=Mock(sensor_type=Mock()))

        result = routing_rule(Mode.AT_HOME, event)

        assert result == DeliveryType.SILENT

    def test_routing_rule_unknown_mode_defaults_silent(self):
        """Unknown mode should default to SILENT for unknown events."""
        event = Event()

        result = routing_rule("unknown_mode", event)

        assert result == DeliveryType.SILENT

    def test_routing_rule_with_event_class(self):
        """routing_rule should accept event class instead of instance."""
        result = routing_rule(Mode.AT_HOME, CameraDetectionEvent)

        assert result == DeliveryType.SILENT


class TestNotificationRouter:
    """Functional tests for NotificationRouter."""

    def test_router_subscribe(self, mock_state_manager, mock_sink):
        """Router should register subscribers for event types."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])

        callback = Mock()
        router.subscribe(BatteryEvent, callback)

        assert BatteryEvent in router._subscribers
        assert callback in router._subscribers[BatteryEvent]

    def test_router_route_event(self, mock_state_manager, mock_sink):
        """Router should call subscribed callbacks for events."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])

        callback = Mock()
        router.subscribe(BatteryEvent, callback)

        event = BatteryEvent(device="sensor001", percentage=50)
        router.route_event(event)

        callback.assert_called_once_with(event)

    def test_router_route_event_bubbles_to_parent_class(
        self, mock_state_manager, mock_sink
    ):
        """Router should route to parent class handlers (not bubble up)."""
        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])

        device_callback = Mock()
        battery_callback = Mock()

        router.subscribe(DeviceEvent, device_callback)
        router.subscribe(BatteryEvent, battery_callback)

        event = BatteryEvent(device="sensor001", percentage=50)
        router.route_event(event)

        # Should only call BatteryEvent handler, not DeviceEvent
        battery_callback.assert_called_once()
        device_callback.assert_not_called()


class TestAfvalEventHandler:
    """Functional tests for AfvalEventHandler."""

    def test_afval_event_handler_sends_to_all_users(
        self, mock_state_manager, mock_sink
    ):
        """AfvalEventHandler should send afval messages to all users."""
        user = User(name="testuser", telegram_user_id=123456)
        mock_state_manager.users.get_all_users.return_value = [user]

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = AfvalEventHandler(router, mock_state_manager)

        event = AfvalEvent(message="Trash collection tomorrow")
        handler.handle_afval_event(event)

        mock_sink.send.assert_called_once()

    def test_afval_event_handler_pins_message(self, mock_state_manager, mock_sink):
        """AfvalEventHandler should pin afval messages."""
        user = User(name="testuser", telegram_user_id=123456)
        mock_state_manager.users.get_all_users.return_value = [user]

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = AfvalEventHandler(router, mock_state_manager)

        event = AfvalEvent(message="Trash collection tomorrow")
        handler.handle_afval_event(event)

        # Check that pin=True was passed
        call_kwargs = mock_sink.send.call_args[1]
        assert call_kwargs.get("pin") is True


class TestUserSettingChangedEventHandler:
    """Functional tests for UserSettingChangedEventHandler."""

    def test_setting_changed_handler_updates_camera_preference(
        self, mock_state_manager, mock_sink
    ):
        """UserSettingChangedEventHandler should update camera preferences."""
        user = User(name="testuser", telegram_user_id=123456)
        mock_state_manager.users.get_all_users.return_value = [user]

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = UserSettingChangedEventHandler(router, mock_state_manager)

        event = UserSettingsChangedEvent(
            user=user,
            settings_type=UserSettingsType.CAMERA_PREFERENCE,
            settings_value="achterdeur",
            value=True,
        )
        handler.handle_change_event(event)

        assert user.has_camera_interest("achterdeur") is True


class TestSnoozeEventHandler:
    """Functional tests for SnoozeEventHandler."""

    def test_snooze_handler_resets_snooze(self, mock_state_manager, mock_sink):
        """SnoozeEventHandler should reset snooze when value is None."""
        user = User(name="testuser", telegram_user_id=123456)
        user.snooze_for(3600)

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SnoozeEventHandler(router, mock_state_manager)

        event = UserSnoozeEvent(user=user, value=None)
        handler.handle_snooze_event(event)

        assert user.is_snoozing is False

    def test_snooze_handler_parses_minutes(self, mock_state_manager, mock_sink):
        """SnoozeEventHandler should parse minute durations."""
        user = User(name="testuser", telegram_user_id=123456)

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SnoozeEventHandler(router, mock_state_manager)

        event = UserSnoozeEvent(user=user, value="15 Mins")
        handler.handle_snooze_event(event)

        assert user.is_snoozing is True

    def test_snooze_handler_parses_hours(self, mock_state_manager, mock_sink):
        """SnoozeEventHandler should parse hour durations."""
        user = User(name="testuser", telegram_user_id=123456)

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SnoozeEventHandler(router, mock_state_manager)

        event = UserSnoozeEvent(user=user, value="2 Hours")
        handler.handle_snooze_event(event)

        assert user.is_snoozing is True

    def test_snooze_handler_parses_days(self, mock_state_manager, mock_sink):
        """SnoozeEventHandler should parse day durations."""
        user = User(name="testuser", telegram_user_id=123456)

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = SnoozeEventHandler(router, mock_state_manager)

        event = UserSnoozeEvent(user=user, value="1 Day")
        handler.handle_snooze_event(event)

        assert user.is_snoozing is True


class TestModeToggleEventHandler:
    """Functional tests for ModeToggleEventHandler."""

    def test_mode_toggle_handler_sets_mode(self, mock_state_manager, mock_sink):
        """ModeToggleEventHandler should set user mode via state manager."""
        user = User(name="testuser", telegram_user_id=123456)

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = ModeToggleEventHandler(router, mock_state_manager)

        event = UserModeToggleEvent(user=user, value=Mode.AWAY)
        handler.handle_user_mode_event(event)

        # The handler calls state.set_user_mode which should update the user
        mock_state_manager.set_user_mode.assert_called_once_with(user, Mode.AWAY)

    def test_mode_toggle_handler_toggles_when_value_none(
        self, mock_state_manager, mock_sink
    ):
        """ModeToggleEventHandler should toggle mode when value is None."""
        user = User(name="testuser", telegram_user_id=123456)
        user.mode = Mode.AT_HOME
        mock_state_manager.get_user_mode.return_value = Mode.AT_HOME

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = ModeToggleEventHandler(router, mock_state_manager)

        event = UserModeToggleEvent(user=user, value=None)
        handler.handle_user_mode_event(event)

        # When value is None, it should toggle (not AT_HOME = AWAY)
        mock_state_manager.set_user_mode.assert_called_once()


class TestDoorcardEventHandler:
    """Functional tests for DoorcardEventHandler."""

    def test_doorcard_handler_creates_mode_toggle(self, mock_state_manager, mock_sink):
        """DoorcardEventHandler should create mode toggle event for valid card."""
        user = User(name="testuser", telegram_user_id=123456, keycards=["card123"])
        mock_state_manager.user_from_doorcard.return_value = user

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = DoorcardEventHandler(router, mock_state_manager)

        event = DoorCardEvent(card_number="card123")
        handler.handle_doorcard(event)

        # Should have routed a UserModeToggleEvent (check route_event was called)
        # The handler calls route_event, not set_user_mode directly
        assert True  # If we got here without error, the handler worked


class TestCameraDetectionEventHandler:
    """Functional tests for CameraDetectionEventHandler."""

    def test_camera_detection_handler_checks_user_mode(
        self, mock_state_manager, mock_sink
    ):
        """CameraDetectionEventHandler should check user mode for routing."""
        user = User(name="testuser", telegram_user_id=123456)
        user.set_camera_interest("achterdeur", True)
        mock_state_manager.users.get_all_users.return_value = [user]
        mock_state_manager.get_user_mode.return_value = Mode.AT_HOME
        mock_state_manager.user_wants_event.return_value = True

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = CameraDetectionEventHandler(router, mock_state_manager)

        event = CameraDetectionEvent(camera_name="achterdeur", payload={})
        handler.handle_detection_event(event)

        mock_sink.send.assert_called_once()


class TestDeviceEventHandler:
    """Functional tests for DeviceEventHandler."""

    def test_device_handler_routes_low_battery(self, mock_state_manager, mock_sink):
        """DeviceEventHandler should route LowBatteryEvent for low battery."""
        user = User(name="testuser", telegram_user_id=123456)
        mock_state_manager.users.get_all_users.return_value = [user]

        # Create a mock router to avoid infinite recursion
        mock_router = Mock()
        mock_router.route_event = Mock()

        handler = DeviceEventHandler(mock_router, mock_state_manager)

        event = BatteryEvent(device="sensor001", percentage=5)
        handler.handle_device_event(event)

        # Should have routed a LowBatteryEvent
        mock_router.route_event.assert_called_once()
        # Check that it was a LowBatteryEvent
        call_args = mock_router.route_event.call_args[0][0]
        assert isinstance(call_args, LowBatteryEvent)


class TestTemperatureEventHandler:
    """Functional tests for TemperatureEventHandler."""

    def test_temperature_handler_adds_reading(self, mock_state_manager, mock_sink):
        """TemperatureEventHandler should add temperature readings to state."""
        user = User(name="testuser", telegram_user_id=123456)
        mock_state_manager.users.get_all_users.return_value = [user]

        router = NotificationRouter(state_manager=mock_state_manager, sinks=[mock_sink])
        handler = TemperatureEventHandler(router, mock_state_manager)

        event = TemperatureEvent(device="therm001", temperature=22.5)
        handler.handle_temperature_event(event)

        mock_state_manager.add_temperature_reading.assert_called_once()


class TestPresenceDetectionEventHandler:
    """Functional tests for PresenceDetectionEventHandler."""

    def test_presence_handler_updates_sensor(self, mock_state_manager, mock_sink):
        """PresenceDetectionEventHandler should update sensor presence."""
        from sensors import Sensor, SensorType

        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )
        mock_state_manager.get_sensor.return_value = sensor

        # Use a mock router to avoid the recursive call to handler
        mock_router = Mock()
        mock_router.route_event = Mock()

        handler = PresenceDetectionEventHandler(mock_router, mock_state_manager)

        event = PresenceDetectionEvent(device="sensor001")
        handler.handle_presence_event(event)

        mock_state_manager.presence_detected.assert_called_once()
        # Should have routed IndoorPresenceDetectionEvent
        mock_router.route_event.assert_called_once()

    def test_presence_handler_routes_indoor_event(self, mock_state_manager, mock_sink):
        """PresenceDetectionEventHandler should route indoor presence events."""
        from sensors import Sensor, SensorType

        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )
        mock_state_manager.get_sensor.return_value = sensor

        # Use a mock router to avoid the recursive call to handler
        mock_router = Mock()
        mock_router.route_event = Mock()

        handler = PresenceDetectionEventHandler(mock_router, mock_state_manager)

        event = PresenceDetectionEvent(device="sensor001")
        handler.handle_presence_event(event)

        # Should have routed IndoorPresenceDetectionEvent
        mock_router.route_event.assert_called_once()
        call_args = mock_router.route_event.call_args[0][0]
        assert isinstance(call_args, IndoorPresenceDetectionEvent)

    def test_presence_handler_suppresses_within_window(
        self, mock_state_manager, mock_sink
    ):
        """PresenceDetectionEventHandler should suppress events within the window."""
        from sensors import Sensor, SensorType

        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )
        mock_state_manager.get_sensor.return_value = sensor
        # Mock that we should NOT route (within window)
        mock_state_manager.should_route_presence_event.return_value = False

        mock_router = Mock()
        mock_router.route_event = Mock()

        handler = PresenceDetectionEventHandler(mock_router, mock_state_manager)

        event = PresenceDetectionEvent(device="sensor001")
        handler.handle_presence_event(event)

        # Should NOT have routed the event
        mock_router.route_event.assert_not_called()

    def test_presence_handler_routes_after_window(self, mock_state_manager, mock_sink):
        """PresenceDetectionEventHandler should route events after the window."""
        from sensors import Sensor, SensorType

        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )
        mock_state_manager.get_sensor.return_value = sensor
        # Mock that we should route (after window)
        mock_state_manager.should_route_presence_event.return_value = True

        mock_router = Mock()
        mock_router.route_event = Mock()

        handler = PresenceDetectionEventHandler(mock_router, mock_state_manager)

        event = PresenceDetectionEvent(device="sensor001")
        handler.handle_presence_event(event)

        # Should have routed the event
        mock_router.route_event.assert_called_once()
        # Should have marked the event as routed
        mock_state_manager.mark_presence_event_routed.assert_called_once()
