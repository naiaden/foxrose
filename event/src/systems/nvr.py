"""Network Video Recorder (NVR) integration for Frigate."""

import requests
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
