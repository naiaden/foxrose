"""Tests for ChangeEvent and its subclasses."""

from events.change_event import (
    ChangeEvent,
    SettingsChangedEvent,
    UserSettingsChangedEvent,
    UserSnoozeEvent,
    UserModeToggleEvent,
    UserSettingsType,
)
from events.event import Event
from users import User
from modes import Mode


class TestUserSettingsType:
    """Functional tests for UserSettingsType enum."""

    def test_settings_type_has_camera_preference(self):
        """UserSettingsType should have CAMERA_PREFERENCE value."""
        assert hasattr(UserSettingsType, "CAMERA_PREFERENCE")

    def test_settings_type_has_mode(self):
        """UserSettingsType should have MODE value."""
        assert hasattr(UserSettingsType, "MODE")

    def test_settings_type_has_snooze(self):
        """UserSettingsType should have SNOOZE value."""
        assert hasattr(UserSettingsType, "SNOOZE")


class TestChangeEvent:
    """Functional tests for ChangeEvent."""

    def test_change_event_inherits_from_event(self):
        """ChangeEvent should be a subclass of Event."""
        event = ChangeEvent()
        assert isinstance(event, Event)

    def test_change_event_str_representation(self):
        """ChangeEvent __str__ should include 'ChangeEvent'."""
        event = ChangeEvent()
        event_str = str(event)

        assert "ChangeEvent" in event_str


class TestSettingsChangedEvent:
    """Functional tests for SettingsChangedEvent."""

    def test_settings_changed_event_str_representation(self):
        """SettingsChangedEvent __str__ should include event type."""
        event = SettingsChangedEvent()
        event_str = str(event)

        assert "SettingsChangedEvent" in event_str


class TestUserSettingsChangedEvent:
    """Functional tests for UserSettingsChangedEvent."""

    def test_user_settings_changed_event_has_user(self):
        """UserSettingsChangedEvent should store user reference."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserSettingsChangedEvent(
            user=user,
            settings_type=UserSettingsType.CAMERA_PREFERENCE,
            settings_value="achterdeur",
            value=True,
        )

        assert event.user == user

    def test_user_settings_changed_event_str_includes_details(self):
        """UserSettingsChangedEvent __str__ should include all details."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserSettingsChangedEvent(
            user=user,
            settings_type=UserSettingsType.CAMERA_PREFERENCE,
            settings_value="achterdeur",
            value=True,
        )
        event_str = str(event)

        assert "testuser" in event_str
        assert "CAMERA_PREFERENCE" in event_str

    def test_user_settings_changed_event_with_optional_value(self):
        """UserSettingsChangedEvent should handle None value."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserSettingsChangedEvent(
            user=user,
            settings_type=UserSettingsType.CAMERA_PREFERENCE,
            settings_value="achterdeur",
            value=None,
        )

        assert event.value is None


class TestUserSnoozeEvent:
    """Functional tests for UserSnoozeEvent."""

    def test_user_snooze_event_defaults_to_snooze_type(self):
        """UserSnoozeEvent should default settings_type to SNOOZE."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserSnoozeEvent(user=user, value=3600)

        assert event.settings_type == UserSettingsType.SNOOZE

    def test_user_snooze_event_str_representation(self):
        """UserSnoozeEvent __str__ should include snooze info."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserSnoozeEvent(user=user, value=3600)
        event_str = str(event)

        assert "UserSnoozeEvent" in event_str
        assert "testuser" in event_str

    def test_user_snooze_event_inherits_from_user_settings_changed(self):
        """UserSnoozeEvent should be a subclass of UserSettingsChangedEvent."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserSnoozeEvent(user=user, value=3600)

        assert isinstance(event, UserSettingsChangedEvent)
        assert isinstance(event, ChangeEvent)
        assert isinstance(event, Event)


class TestUserModeToggleEvent:
    """Functional tests for UserModeToggleEvent."""

    def test_user_mode_toggle_event_defaults_to_mode_type(self):
        """UserModeToggleEvent should default settings_type to MODE."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserModeToggleEvent(user=user, value=Mode.AWAY)

        assert event.settings_type == UserSettingsType.MODE

    def test_user_mode_toggle_event_str_representation(self):
        """UserModeToggleEvent __str__ should include mode toggle info."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserModeToggleEvent(user=user, value=Mode.AWAY)
        event_str = str(event)

        assert "UserModeToggleEvent" in event_str
        assert "testuser" in event_str

    def test_user_mode_toggle_event_inherits_from_user_settings_changed(self):
        """UserModeToggleEvent should be a subclass of UserSettingsChangedEvent."""
        user = User(name="testuser", telegram_user_id=123456)
        event = UserModeToggleEvent(user=user, value=Mode.AWAY)

        assert isinstance(event, UserSettingsChangedEvent)
        assert isinstance(event, ChangeEvent)
        assert isinstance(event, Event)
