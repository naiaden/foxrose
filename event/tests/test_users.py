"""Tests for User and UserManager classes."""

from datetime import datetime, timedelta

from users import User, UserManager
from modes import Mode
from events.detection_event import CameraDetectionEvent, PresenceDetectionEvent
from events.event import Event


class TestUser:
    """Functional tests for User class."""

    def test_user_str_representation(self):
        """User __str__ should return name in brackets."""
        user = User(name="testuser")

        assert str(user) == "[testuser]"

    def test_user_default_mode_is_at_home(self):
        """User should default to AT_HOME mode."""
        user = User(name="testuser")

        assert user.mode == Mode.AT_HOME

    def test_user_can_set_mode(self):
        """User should be able to change mode."""
        user = User(name="testuser")
        user.mode = Mode.AWAY

        assert user.mode == Mode.AWAY

    def test_user_default_not_snoozing(self):
        """User should not be snoozing by default."""
        user = User(name="testuser")

        assert user.is_snoozing is False

    def test_user_snooze_until(self):
        """User should be snoozing after snooze_until is called."""
        user = User(name="testuser")
        future_time = datetime.now() + timedelta(hours=1)
        user.snooze_until(future_time)

        assert user.is_snoozing is True

    def test_user_snooze_for(self):
        """User should be snoozing after snooze_for is called."""
        user = User(name="testuser")
        user.snooze_for(3600)  # 1 hour

        assert user.is_snoozing is True

    def test_user_reset_snooze(self):
        """User should stop snoozing after reset_snooze is called."""
        user = User(name="testuser")
        user.snooze_for(3600)
        user.reset_snooze()

        assert user.is_snoozing is False

    def test_user_snooze_expiry(self):
        """User should stop snoozing after snooze period expires."""
        user = User(name="testuser")
        user.snooze_for(0)  # Immediate expiry

        # Small delay to ensure time passes
        import time

        time.sleep(0.1)

        assert user.is_snoozing is False

    def test_user_default_camera_interest_is_false(self):
        """User should not be interested in cameras by default."""
        user = User(name="testuser")

        assert user.has_camera_interest("achterdeur") is False

    def test_user_set_camera_interest(self):
        """User should be able to set camera interest."""
        user = User(name="testuser")
        user.set_camera_interest("achterdeur", True)

        assert user.has_camera_interest("achterdeur") is True

    def test_user_camera_interest_defaults_to_true(self):
        """User set_camera_interest should default to True."""
        user = User(name="testuser")
        user.set_camera_interest("achterdeur")

        assert user.has_camera_interest("achterdeur") is True

    def test_user_uses_keycard(self):
        """User should recognize their keycards."""
        user = User(name="testuser", keycards=["card123", "card456"])

        assert user.uses_keycard("card123") is True
        assert user.uses_keycard("card456") is True
        assert user.uses_keycard("unknown") is False

    def test_user_add_keycard(self):
        """User should be able to add keycards."""
        user = User(name="testuser")
        user.add_keycard("newcard")

        assert user.uses_keycard("newcard") is True

    def test_user_wants_notification_when_not_snoozing(self):
        """User should want notifications when not snoozing."""
        user = User(name="testuser")

        assert user.wants_notification(Event()) is True

    def test_user_wants_notification_when_snoozing(self):
        """User should not want notifications when snoozing."""
        user = User(name="testuser")
        user.snooze_for(3600)

        assert user.wants_notification(Event()) is False

    def test_user_wants_notification_indoor_presence_at_home(self):
        """User should not want presence notifications when at home (mode check)."""
        # The wants_notification method checks mode for PresenceDetectionEvent
        # but the event type check is for PresenceDetectionEvent, not IndoorPresenceDetectionEvent
        user = User(name="testuser")
        user.mode = Mode.AT_HOME
        event = PresenceDetectionEvent(device="sensor001")

        # PresenceDetectionEvent check: mode != AT_HOME returns True
        assert user.wants_notification(event) is False

    def test_user_wants_notification_indoor_presence_away(self):
        """User should want presence notifications when away (mode check)."""
        user = User(name="testuser")
        user.mode = Mode.AWAY
        event = PresenceDetectionEvent(device="sensor001")

        # PresenceDetectionEvent check: mode != AT_HOME returns True
        assert user.wants_notification(event) is True

    def test_user_wants_notification_camera_with_interest(self):
        """User should want camera notifications for interested cameras."""
        user = User(name="testuser")
        user.set_camera_interest("achterdeur", True)
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        assert user.wants_notification(event) is True

    def test_user_wants_notification_camera_without_interest(self):
        """User should not want camera notifications for uninterested cameras."""
        user = User(name="testuser")
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        assert user.wants_notification(event) is False


class TestUserManager:
    """Functional tests for UserManager class."""

    def test_user_manager_get_user(self):
        """UserManager should retrieve users by name."""
        user = User(name="testuser")
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        assert manager.get_user("testuser") == user

    def test_user_manager_get_user_not_found(self):
        """UserManager should return None for unknown users."""
        user = User(name="testuser")
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        assert manager.get_user("unknown") is None

    def test_user_manager_is_allowed(self):
        """UserManager should check if user is allowed."""
        user = User(name="testuser")
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        assert manager.is_allowed(user) is True

    def test_user_manager_get_all_users(self):
        """UserManager should return all users."""
        user1 = User(name="user1")
        user2 = User(name="user2")
        manager = UserManager(
            users=[user1, user2], allowed_user_names=["user1", "user2"]
        )

        all_users = manager.get_all_users()

        assert len(all_users) == 2
        assert user1 in all_users
        assert user2 in all_users

    def test_user_manager_set_user_mode(self):
        """UserManager should update user mode."""
        user = User(name="testuser")
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        manager.set_user_mode(user, Mode.AWAY)

        assert user.mode == Mode.AWAY

    def test_user_manager_get_user_mode(self):
        """UserManager should retrieve user mode."""
        user = User(name="testuser")
        user.mode = Mode.NIGHT
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        assert manager.get_user_mode(user) == Mode.NIGHT

    def test_user_manager_get_user_from_telegram_id(self):
        """UserManager should find user by telegram ID."""
        user = User(name="testuser", telegram_user_id=123456789)
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        found = manager.get_user_from_telegram_id(123456789)

        assert found == user

    def test_user_manager_get_user_from_telegram_id_not_found(self):
        """UserManager should return None for unknown telegram ID."""
        user = User(name="testuser", telegram_user_id=123456789)
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        assert manager.get_user_from_telegram_id(999999999) is None

    def test_user_manager_get_user_from_doorcard(self):
        """UserManager should find user by doorcard ID."""
        user = User(name="testuser", keycards=["card123"])
        manager = UserManager(users=[user], allowed_user_names=["testuser"])

        found = manager.get_user_from_doorcard("card123")

        assert found == user

    def test_user_manager_from_env_string(self):
        """UserManager.from_env_string should parse user definitions."""
        # Format: "username:T123456:Kcard1,card2"
        users = UserManager.from_env_string("testuser:T123456:Kcard123,card456")

        assert len(users) == 1
        assert users[0].name == "testuser"
        assert users[0].telegram_user_id == 123456
        assert "card123" in users[0].keycards
        assert "card456" in users[0].keycards

    def test_user_manager_from_env_string_multiple_users(self):
        """UserManager.from_env_string should handle multiple users."""
        users = UserManager.from_env_string("user1:T111:Kcard1;user2:T222:Kcard2")

        assert len(users) == 2
        assert users[0].name == "user1"
        assert users[1].name == "user2"

    def test_user_manager_from_env_string_no_telegram_id(self):
        """UserManager.from_env_string should handle users without telegram ID."""
        users = UserManager.from_env_string("testuser:Kcard123")

        assert len(users) == 1
        assert users[0].telegram_user_id is None

    def test_user_manager_from_env_string_no_keycards(self):
        """UserManager.from_env_string should handle users without keycards."""
        users = UserManager.from_env_string("testuser:T123456")

        assert len(users) == 1
        assert users[0].keycards == set()
