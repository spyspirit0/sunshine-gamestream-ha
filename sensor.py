"""
Sunshine Game Stream Sensor Platform
Monitors Sunshine /api/logs endpoint to detect active streaming sessions
"""

import logging
import requests
import re
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_NAME

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sunshine_gamestream"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sunshine Game Stream sensor from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    scan_interval_seconds = entry.data.get(CONF_SCAN_INTERVAL, 2)
    server_name = entry.data.get(CONF_NAME, "Sunshine Server")
    sunshine_version = entry.data.get("sunshine_version", "Unknown")

    # Create API wrapper
    sunshine_api = SunshineLogsAPI(host, port, username, password)

    # Create coordinator with custom update interval
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"sunshine_{host}",
        update_method=sunshine_api.async_get_status,
        update_interval=timedelta(seconds=scan_interval_seconds),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Create sensor
    async_add_entities([
        SunshineStatusSensor(
            coordinator,
            sunshine_api,
            entry.entry_id,
            server_name,
            sunshine_version
        )
    ])


class SunshineLogsAPI:
    """Interface to Sunshine /api/logs endpoint."""

    def __init__(self, host, port, username=None, password=None):
        """Initialize the API wrapper."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"https://{host}:{port}"
        self.session = requests.Session()
        self.session.verify = False

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.is_streaming = False
        self.last_log_check = ""

    async def async_get_status(self):
        """Async wrapper for get_status."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_status)

    def get_logs(self):
        """Fetch logs from /api/logs endpoint."""
        try:
            url = f"{self.base_url}/api/logs"
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)

            response = self.session.get(url, auth=auth, timeout=10)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as err:
            _LOGGER.error(f"Error fetching logs: {err}")
            return None

    def parse_logs(self, logs):
        """Parse log content to detect streaming status."""
        if not logs:
            return

        if self.last_log_check and self.last_log_check in logs:
            split_pos = logs.rfind(self.last_log_check)
            new_logs = logs[split_pos + len(self.last_log_check):]
        else:
            new_logs = '\n'.join(logs.split('\n')[-50:])

        log_lines = logs.strip().split('\n')
        if log_lines:
            self.last_log_check = log_lines[-1]

        stream_start_patterns = [
            r"CLIENT CONNECTED",
            r"New streaming session started",
        ]

        stream_stop_patterns = [
            r"CLIENT DISCONNECTED",
        ]

        for pattern in stream_start_patterns:
            if re.search(pattern, new_logs, re.IGNORECASE):
                if not self.is_streaming:
                    _LOGGER.info(f"Detected streaming START")
                self.is_streaming = True
                break

        for pattern in stream_stop_patterns:
            if re.search(pattern, new_logs, re.IGNORECASE):
                if self.is_streaming:
                    _LOGGER.info(f"Detected streaming STOP")
                self.is_streaming = False
                break

    def get_status(self):
        """Get current streaming status."""
        logs = self.get_logs()

        if logs is None:
            return None

        self.parse_logs(logs)

        return {
            "is_streaming": self.is_streaming,
        }


class SunshineStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing if Sunshine is actively streaming."""

    def __init__(self, coordinator, api, entry_id, server_name,
                 sunshine_version):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._server_name = server_name
        self._sunshine_version = sunshine_version

        name_slug = server_name.lower().replace(" ", "_").replace("-", "_")
        name_slug = re.sub(r'[^a-z0-9_]', '', name_slug)

        self._attr_name = f"{server_name} Sunshine Status"
        self._attr_unique_id = f"sunshine_gamestream_{name_slug}_status"
        self._entry_id = entry_id

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._api.host)},
            "name": self._server_name,
            "manufacturer": "Sunshine Game Stream Integration",
            "model": "Sunshine Server",
            "sw_version": self._sunshine_version,
        }

    @property
    def state(self):
        """Return the state."""
        if self.coordinator.data is None:
            return "unavailable"
        return "streaming" if self.coordinator.data.get(
            "is_streaming") else "idle"

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:television-shimmer" if self.state == "streaming" else "mdi:cast-off"

