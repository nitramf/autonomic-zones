from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import DEFAULT_NAMES, DEFAULT_PORT, DEFAULT_ZONES, DOMAIN

class AutonomicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                zones = [int(x.strip()) for x in user_input["zones"].split(",")]
                names = [x.strip() for x in user_input["names"].split(",")]
                if len(zones) != 4:
                    raise ValueError("exactly four zones required")
                if len(names) != 4:
                    raise ValueError("exactly four names required")
                if any(z < 0 or z > 95 for z in zones):
                    raise ValueError("zone must be 0..95")
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Autonomic M401 ({user_input[CONF_HOST]})",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        "port": user_input["port"],
                        "zones": zones,
                        "zone_names": names,
                    },
                )
            except Exception:
                errors["base"] = "invalid_config"

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required("port", default=DEFAULT_PORT): vol.Coerce(int),
            vol.Required("zones", default=",".join(map(str, DEFAULT_ZONES))): str,
            vol.Required("names", default=",".join(DEFAULT_NAMES)): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
