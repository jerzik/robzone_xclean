"""Config flow for Robzone Duoro Xclean LAN."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import CONF_AUTH_CODE, CONF_TARGET_ID, DEFAULT_PORT, DOMAIN


class RobzoneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Robzone Duoro Xclean LAN."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_TARGET_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get("name", "Robzone Duoro Xclean 5"),
                data={
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_AUTH_CODE: user_input[CONF_AUTH_CODE],
                    CONF_TARGET_ID: user_input[CONF_TARGET_ID],
                },
            )

        schema = vol.Schema(
            {
                vol.Optional("name", default="Robzone Duoro Xclean 5"): str,
                vol.Required(CONF_HOST, default="192.168.2.69"): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_AUTH_CODE): str,
                vol.Required(CONF_TARGET_ID): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
