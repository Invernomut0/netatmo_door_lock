"""Config flow for Netatmo Door Lock integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .utils import get_token
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("Username"): cv.string,
        vol.Required("password"): cv.string,
    }
)


class NDLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Netatmo Door Lock."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the credentials
                token_data = await self.hass.async_add_executor_job(
                    get_token, user_input["Username"], user_input["password"]
                )

                if token_data and "access_token" in token_data:
                    # Check if already configured
                    await self.async_set_unique_id(user_input["Username"])
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="Netatmo Door Lock",
                        data={
                            "Username": user_input["Username"],
                            "Password": user_input["password"],
                        },
                    )
                else:
                    errors["base"] = "invalid_auth"

            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", str(ex))
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
