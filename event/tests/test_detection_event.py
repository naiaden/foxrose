"""Tests for DetectionEvent and its subclasses."""

from events.detection_event import (
    DetectionEvent,
    CameraDetectionEvent,
    PresenceDetectionEvent,
    IndoorPresenceDetectionEvent,
    OutdoorPresenceDetectionEvent,
    DetectionConfidence,
)
from events.event import Event
from sensors import Sensor, SensorType


class TestDetectionEvent:
    """Functional tests for DetectionEvent."""

    def test_detection_event_inherits_from_event(self):
        """DetectionEvent should be a subclass of Event."""
        event = DetectionEvent()
        assert isinstance(event, Event)

    def test_detection_event_str_representation(self):
        """DetectionEvent __str__ should include 'DetectionEvent'."""
        event = DetectionEvent()
        event_str = str(event)

        assert "DetectionEvent" in event_str


class TestDetectionConfidence:
    """Functional tests for DetectionConfidence enum."""

    def test_confidence_from_duration_ignore(self):
        """Very short duration should return IGNORE confidence."""
        assert DetectionConfidence.from_duration(0.5) == DetectionConfidence.IGNORE
        assert DetectionConfidence.from_duration(0.9) == DetectionConfidence.IGNORE

    def test_confidence_from_duration_maybe(self):
        """1+ second duration should return MAYBE confidence."""
        assert DetectionConfidence.from_duration(1.0) == DetectionConfidence.MAYBE
        assert DetectionConfidence.from_duration(1.5) == DetectionConfidence.MAYBE

    def test_confidence_from_duration_likely(self):
        """2+ second duration should return LIKELY confidence (uses > not >=)."""
        assert DetectionConfidence.from_duration(2.1) == DetectionConfidence.LIKELY
        assert DetectionConfidence.from_duration(3.0) == DetectionConfidence.LIKELY

    def test_confidence_from_duration_confident(self):
        """5+ second duration should return CONFIDENT confidence (uses > not >=)."""
        assert DetectionConfidence.from_duration(5.1) == DetectionConfidence.CONFIDENT
        assert DetectionConfidence.from_duration(7.0) == DetectionConfidence.CONFIDENT

    def test_confidence_from_duration_loitering(self):
        """10+ second duration should return LOITERING confidence (uses > not >=)."""
        assert DetectionConfidence.from_duration(10.1) == DetectionConfidence.LOITERING
        assert DetectionConfidence.from_duration(15.0) == DetectionConfidence.LOITERING


class TestCameraDetectionEvent:
    """Functional tests for CameraDetectionEvent."""

    def test_camera_detection_event_has_camera_name(self):
        """CameraDetectionEvent should store camera name."""
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        assert event.camera_name == "achterdeur"

    def test_camera_detection_event_has_payload(self):
        """CameraDetectionEvent should store payload dict."""
        payload = {"event_id": "123", "confidence": 0.95}
        event = CameraDetectionEvent(camera_name="achterdeur", payload=payload)

        assert event.payload == payload

    def test_camera_detection_event_str_representation(self):
        """CameraDetectionEvent __str__ should include camera name."""
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})
        event_str = str(event)

        assert "achterdeur" in event_str
        assert "CameraDetectionEvent" in event_str

    def test_camera_detection_event_inherits_from_detection_event(self):
        """CameraDetectionEvent should be a subclass of DetectionEvent."""
        event = CameraDetectionEvent(camera_name="achterdeur", payload={})

        assert isinstance(event, DetectionEvent)
        assert isinstance(event, Event)


class TestPresenceDetectionEvent:
    """Functional tests for PresenceDetectionEvent."""

    def test_presence_detection_event_has_device(self):
        """PresenceDetectionEvent should store device identifier."""
        event = PresenceDetectionEvent(device="sensor001")

        assert event.device == "sensor001"

    def test_presence_detection_event_str_representation(self):
        """PresenceDetectionEvent __str__ should include device."""
        event = PresenceDetectionEvent(device="sensor001")
        event_str = str(event)

        assert "sensor001" in event_str
        assert "PresenceDetectionEvent" in event_str


class TestIndoorPresenceDetectionEvent:
    """Functional tests for IndoorPresenceDetectionEvent."""

    def test_indoor_presence_event_uses_sensor_object(self):
        """IndoorPresenceDetectionEvent should accept a Sensor object."""
        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )
        event = IndoorPresenceDetectionEvent(device=sensor)

        assert event.device == sensor
        assert event.device.sensor_type == SensorType.INDOOR

    def test_indoor_presence_event_str_representation(self):
        """IndoorPresenceDetectionEvent __str__ should indicate indoor presence."""
        sensor = Sensor(
            device_id="sensor001", name="Living Room", sensor_type=SensorType.INDOOR
        )
        event = IndoorPresenceDetectionEvent(device=sensor)
        event_str = str(event)

        assert "IndoorPresenceDetectionEvent" in event_str


class TestOutdoorPresenceDetectionEvent:
    """Functional tests for OutdoorPresenceDetectionEvent."""

    def test_outdoor_presence_event_uses_sensor_object(self):
        """OutdoorPresenceDetectionEvent should accept a Sensor object."""
        sensor = Sensor(
            device_id="sensor002", name="Garden", sensor_type=SensorType.OUTDOOR
        )
        event = OutdoorPresenceDetectionEvent(device=sensor)

        assert event.device == sensor
        assert event.device.sensor_type == SensorType.OUTDOOR

    def test_outdoor_presence_event_str_representation(self):
        """OutdoorPresenceDetectionEvent __str__ should indicate outdoor presence."""
        sensor = Sensor(
            device_id="sensor002", name="Garden", sensor_type=SensorType.OUTDOOR
        )
        event = OutdoorPresenceDetectionEvent(device=sensor)
        event_str = str(event)

        assert "OutdoorPresenceDetectionEvent" in event_str
