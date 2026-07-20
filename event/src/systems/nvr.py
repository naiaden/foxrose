"""Network Video Recorder (NVR) integration for Frigate."""

import requests
import time
from typing import Optional
from logging_config import logger


class FrigateNVR:
    """Interface for Frigate NVR snapshot retrieval."""

    def __init__(self, server_address: str):
        """
        Initialize Frigate NVR interface.

        Args:
            server_address: IP or hostname of the Frigate server
        """
        self.server_address = server_address
        self.base_url = f"https://{server_address}:8971/api"

    def get_snapshot(self, camera_name: str) -> Optional[bytes]:
        """
        Fetch the latest snapshot from a camera.

        Args:
            camera_name: Name of the camera (e.g., "achterdeur", "voordeur")

        Returns:
            Image bytes if successful, None otherwise
        """
        url = f"{self.base_url}/{camera_name.lower()}/latest.jpg"

        try:
            response = requests.get(url, verify=False, timeout=10)
            if response.status_code == 200:
                logger.debug(f"Successfully fetched snapshot from {camera_name}")
                return response.content
            else:
                logger.warning(
                    f"Failed to fetch snapshot from {camera_name}: "
                    f"Status {response.status_code}"
                )
                return None
        except Exception as e:
            logger.error(f"Error fetching snapshot from {camera_name}: {e}")
            return None

    def get_highres_snapshot(self, camera_name: str) -> Optional[bytes]:
        """
        Get a high-resolution snapshot frame from recording history.

        Fetches the frame from a slightly buffered timestamp (5-10 seconds ago)
        to ensure Frigate has flushed the recording segment to disk.
        """
        try:
            # Query recordings from slightly in the past (e.g. 10s ago)
            # to guarantee the segment is written and available.
            target_time = time.time() - 10.0

            recordings_url = f"{self.base_url}/{camera_name.lower()}/recordings"

            response = requests.get(
                recordings_url,
                verify=False,
                timeout=10,
            )
            response.raise_for_status()

            recordings = response.json()

            if not recordings:
                logger.warning(f"No recordings found for {camera_name}")
                return None

            selected_segment = None

            # Look for a segment that contains our target timestamp
            for segment in recordings:
                start = segment["start_time"]
                end = segment["end_time"]
                if start <= target_time <= end:
                    selected_segment = segment
                    break

            # If current buffered time isn't found, fall back to the newest completed segment
            if selected_segment is None:
                selected_segment = max(recordings, key=lambda r: r["end_time"])
                # Pick a point safely inside the segment (1 second before it ends)
                frame_time = max(
                    selected_segment["start_time"], selected_segment["end_time"] - 1.0
                )
            else:
                frame_time = target_time

            snapshot_url = (
                f"{self.base_url}/"
                f"{camera_name.lower()}/recordings/"
                f"{frame_time:.2f}/snapshot.jpg"  # 'jpg' or 'png' work fine here
            )

            snapshot_response = requests.get(
                snapshot_url,
                verify=False,
                timeout=10,
            )

            if snapshot_response.status_code == 200:
                logger.debug(f"Fetched high-res snapshot for {camera_name}")
                return snapshot_response.content

            logger.warning(
                f"Snapshot request failed ({snapshot_response.status_code}): {snapshot_response.text}"
            )
            return None

        except Exception as e:
            logger.error(f"Error fetching high-res snapshot for {camera_name}: {e}")
            return None
