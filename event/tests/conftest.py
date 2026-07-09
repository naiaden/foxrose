import pytest
from unittest.mock import Mock
import os

# Add src to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Set required environment variables for imports
os.environ.setdefault("lightapi_server", "http://localhost:8000")

from users import User, UserManager
from modes import Mode
from sensors import Sensor, SensorType


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        name="testuser", telegram_user_id=123456789, keycards=["card123", "card456"]
    )


@pytest.fixture
def sample_user_manager(sample_user):
    """Create a user manager with a sample user."""
    return UserManager(users=[sample_user], allowed_user_names=["testuser"])


@pytest.fixture
def sample_sensor():
    """Create a sample indoor sensor."""
    return Sensor(
        device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
    )


@pytest.fixture
def sample_outdoor_sensor():
    """Create a sample outdoor sensor."""
    return Sensor(device_id="sensor002", name="Garden", sensor_type=SensorType.OUTDOOR)


@pytest.fixture
def sample_sensors():
    """Create a list of sample sensors for SensorSystem."""
    return [
        Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        ),
        Sensor(device_id="sensor002", name="Garden", sensor_type=SensorType.OUTDOOR),
    ]


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for router tests."""
    mock = Mock()
    mock.users = Mock()
    mock.users.get_all_users.return_value = []
    mock.get_user_mode.return_value = Mode.AT_HOME
    mock.user_wants_event.return_value = True
    return mock


@pytest.fixture
def mock_sink():
    """Create a mock notification sink."""
    sink = Mock()
    sink.send = Mock()
    return sink
