import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

DOMAIN = "ndl_sensor"


class NDLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NDLFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="NetatmoDoorLock",
                data={
                    "Username": user_input["Username"],
                    "Password": user_input["Password"],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "Username",
                    ): cv.string,
                    vol.Required(
                        "Password",
                    ): cv.string,
                },
            ),
        )


class NDLFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("password"): str})
        )
