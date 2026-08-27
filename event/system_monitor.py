#!/usr/bin/env python3
"""System monitor daemon that publishes system metrics to MQTT."""

import argparse
import json
import logging
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path

import paho.mqtt.client as mqtt
import psutil

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SystemMonitorConfig:
    """Configuration for system monitoring thresholds."""

    cpu_threshold: float = 80.0
    swap_threshold: float = 90.0
    tmp_threshold: float = 90.0
    check_interval: int = 60
    mqtt_server: str = "localhost"
    mqtt_port: int = 1883


class SystemMonitor:
    def __init__(self, config: SystemMonitorConfig):
        self.config = config
        self.hostname = socket.gethostname()
        self.running = False

        # Setup MQTT client
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.enable_logger(logger)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info(f"Connected to MQTT broker at {self.config.mqtt_server}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")

    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.mqtt_client.connect(self.config.mqtt_server, self.config.mqtt_port, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

    def _publish(self, topic: str, payload: dict):
        """Publish message to MQTT topic."""
        try:
            message = json.dumps(payload)
            self.mqtt_client.publish(topic, message, qos=0, retain=False)
            logger.debug(f"Published to {topic}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")

    def check_cpu(self):
        """Check CPU usage and publish if above threshold."""
        cpu_percent = psutil.cpu_percent(interval=1)

        if cpu_percent >= self.config.cpu_threshold:
            logger.warning(f"High CPU usage detected: {cpu_percent}%")
            self._publish(
                f"foxrosehip/system/{self.hostname}/cpu",
                {
                    "hostname": self.hostname,
                    "cpu_percentage": cpu_percent,
                    "threshold": self.config.cpu_threshold,
                },
            )

    def check_swap(self):
        """Check swap usage and publish if above threshold."""
        swap = psutil.swap_memory()
        swap_percent = swap.percent

        if swap_percent >= self.config.swap_threshold:
            logger.warning(f"High swap usage detected: {swap_percent}%")
            self._publish(
                f"foxrosehip/system/{self.hostname}/swap",
                {
                    "hostname": self.hostname,
                    "swap_percentage": swap_percent,
                    "threshold": self.config.swap_threshold,
                },
            )

    def check_tmp(self):
        """Check /tmp disk usage and publish if above threshold."""
        tmp_usage = psutil.disk_usage("/tmp")
        tmp_percent = tmp_usage.percent

        if tmp_percent >= self.config.tmp_threshold:
            logger.warning(f"High /tmp usage detected: {tmp_percent}%")
            self._publish(
                f"foxrosehip/system/{self.hostname}/tmp",
                {
                    "hostname": self.hostname,
                    "tmp_percentage": tmp_percent,
                    "threshold": self.config.tmp_threshold,
                    "path": "/tmp",
                },
            )

    def run_checks(self):
        """Run all system checks."""
        self.check_cpu()
        self.check_swap()
        self.check_tmp()

    def start(self):
        """Start the monitoring loop."""
        self.running = True
        logger.info(f"Starting system monitor for {self.hostname}")
        logger.info(
            f"Thresholds - CPU: {self.config.cpu_threshold}%, "
            f"Swap: {self.config.swap_threshold}%, "
            f"Tmp: {self.config.tmp_threshold}%"
        )

        while self.running:
            try:
                self.run_checks()
                time.sleep(self.config.check_interval)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                time.sleep(self.config.check_interval)

    def stop(self):
        """Stop the monitoring loop."""
        self.running = False


def load_config_from_env() -> SystemMonitorConfig:
    """Load configuration from environment variables."""
    return SystemMonitorConfig(
        cpu_threshold=float(os.environ.get("SYSTEM_MONITOR_CPU_THRESHOLD", "80.0")),
        swap_threshold=float(os.environ.get("SYSTEM_MONITOR_SWAP_THRESHOLD", "90.0")),
        tmp_threshold=float(os.environ.get("SYSTEM_MONITOR_TMP_THRESHOLD", "90.0")),
        check_interval=int(os.environ.get("SYSTEM_MONITOR_CHECK_INTERVAL", "60")),
        mqtt_server=os.environ.get("SYSTEM_MONITOR_MQTT_SERVER", "localhost"),
        mqtt_port=int(os.environ.get("SYSTEM_MONITOR_MQTT_PORT", "1883")),
    )


def main():
    parser = argparse.ArgumentParser(description="System monitor daemon")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config file (optional)",
    )
    parser.add_argument(
        "--mqtt-server",
        type=str,
        default=None,
        help="MQTT broker address",
    )
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=None,
        help="CPU usage threshold (percentage)",
    )
    parser.add_argument(
        "--swap-threshold",
        type=float,
        default=None,
        help="Swap usage threshold (percentage)",
    )
    parser.add_argument(
        "--tmp-threshold",
        type=float,
        default=None,
        help="/tmp usage threshold (percentage)",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=None,
        help="Check interval in seconds",
    )

    args = parser.parse_args()

    # Load config
    if args.config and Path(args.config).exists():
        # TODO: Implement YAML config loading if needed
        logger.info("Config file specified but not yet implemented, using env vars")
        config = load_config_from_env()
    else:
        config = load_config_from_env()

    # Override with command line arguments
    if args.mqtt_server:
        config.mqtt_server = args.mqtt_server
    if args.cpu_threshold is not None:
        config.cpu_threshold = args.cpu_threshold
    if args.swap_threshold is not None:
        config.swap_threshold = args.swap_threshold
    if args.tmp_threshold is not None:
        config.tmp_threshold = args.tmp_threshold
    if args.check_interval is not None:
        config.check_interval = args.check_interval

    # Create and start monitor
    monitor = SystemMonitor(config)

    if not monitor.connect():
        logger.error("Failed to connect to MQTT broker, exiting")
        return

    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        monitor.stop()
        monitor.disconnect()


if __name__ == "__main__":
    main()
