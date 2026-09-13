from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client import AutonomicClient
from .const import DOMAIN

PLATFORMS = [
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = AutonomicClient(
        entry.data["host"],
        entry.data["port"],
        entry.data["zones"],
    )
    await client.start()
    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    client = entry.runtime_data
    await client.stop()
    return ok
