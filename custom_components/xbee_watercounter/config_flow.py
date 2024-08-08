"""Adds config flow for xbee_watercounter."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from . import CONF_DEVICE_IEEE
from .const import DOMAIN
from .coordinator import XBeeWatercounterApiClient


class XBeeWatercounterConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for XBee Watercounter."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                client = XBeeWatercounterApiClient(
                    self.hass, user_input[CONF_DEVICE_IEEE]
                )
                unique_id = await client.async_command("unique_id")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                client.stop()
            except Exception as err:
                _errors["base"] = str(err)
                client.stop()
            else:
                device_ieee = user_input[CONF_DEVICE_IEEE]
                return self.async_create_entry(
                    title=device_ieee,
                    data={
                        CONF_DEVICE_IEEE: device_ieee,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE_IEEE): str}),
            errors=_errors,
        )
