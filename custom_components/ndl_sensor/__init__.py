"""The Netatmo Door Lock integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .utils import get_token

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ndl_sensor"

CONF_USERNAME = "Username"
CONF_PASSWORD = "Password"

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Netatmo Door Lock component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Netatmo Door Lock from a config entry."""
    # Store data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Verify credentials
    try:
        token_data = await hass.async_add_executor_job(
            get_token, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
        )
        if not token_data or "access_token" not in token_data:
            _LOGGER.error("Invalid credentials")
            return False
    except Exception as ex:
        _LOGGER.error("Error authenticating: %s", ex)
        return False

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}

        # Migration changes here if needed
        # Example:
        # new["new_field"] = "default_value"

        hass.config_entries.async_update_entry(config_entry, data=new, version=2)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
