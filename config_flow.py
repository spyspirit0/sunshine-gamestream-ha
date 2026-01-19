"""Config flow for Sunshine Game Stream integration."""
import logging
import voluptuous as vol
import requests
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "sunshine_gamestream"
DEFAULT_PORT = 47990
DEFAULT_SCAN_INTERVAL = 2
DEFAULT_NAME = "Sunshine Server"


class SunshineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sunshine Game Stream."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step where user enters connection details."""
        errors = {}

        if user_input is not None:
            # Check if this host is already configured
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            
            # Validate the connection
            try:
                # Test connection to Sunshine
                url = f"https://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/api/config"
                
                # Prepare authentication if provided
                auth = None
                if user_input.get(CONF_USERNAME) and user_input.get(CONF_PASSWORD):
                    auth = (user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                
                # Create session and disable SSL verification (Sunshine uses self-signed certs)
                session = requests.Session()
                session.verify = False
                
                # Disable SSL warnings
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                # Test the connection
                response = await self.hass.async_add_executor_job(
                    lambda: session.get(url, auth=auth, timeout=10)
                )
                
                # Try to get Sunshine version from config
                sunshine_version = "Unknown"
                if response.status_code == 200:
                    try:
                        config_data = response.json()
                        sunshine_version = config_data.get("version", "Unknown")
                    except:
                        pass
                
                if response.status_code == 401:
                    errors["base"] = "invalid_auth"
                elif response.status_code == 404:
                    # API endpoint not found, but connection works
                    # Try the logs endpoint instead
                    url_logs = f"https://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/api/logs"
                    response = await self.hass.async_add_executor_job(
                        lambda: session.get(url_logs, auth=auth, timeout=10)
                    )
                    if response.status_code == 401:
                        errors["base"] = "invalid_auth"
                    elif response.status_code != 200:
                        errors["base"] = "cannot_connect"
                elif response.status_code != 200:
                    errors["base"] = "cannot_connect"
                
                if not errors:
                    # Add version to user_input for storage
                    user_input["sunshine_version"] = sunshine_version
                    
                    # Use custom name or default
                    server_name = user_input.get(CONF_NAME, DEFAULT_NAME)
                    
                    # Success! Create the config entry
                    return self.async_create_entry(
                        title=server_name,
                        data=user_input
                    )
                    
            except requests.exceptions.ConnectionError:
                errors["base"] = "cannot_connect"
            except requests.exceptions.Timeout:
                errors["base"] = "timeout"
            except Exception as err:
                _LOGGER.exception("Unexpected exception during setup: %s", err)
                errors["base"] = "unknown"

        # Show the configuration form
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Optional(CONF_USERNAME): str,
            vol.Optional(CONF_PASSWORD): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
