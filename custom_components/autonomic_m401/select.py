from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client = entry.runtime_data
    names = entry.data["zone_names"]
    async_add_entities([
        AutonomicSource(client, zone, names[i])
        for i, zone in enumerate(client.zones)
    ])

class AutonomicSource(SelectEntity):
    _attr_has_entity_name = True
    _attr_options = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
    _attr_icon = "mdi:audio-input-rca"

    def __init__(self, client, zone, room_name):
        self._client = client
        self._zone = zone
        self._attr_name = "Source"
        self._attr_unique_id = f"autonomic_m401_zone_{zone}_source"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"zone_{zone}")},
            "name": f"Autonomic M401 – {room_name}",
            "manufacturer": "Autonomic",
            "model": "M401",
        }
        self._client.add_listener(self._on_zone_update)

    @property
    def current_option(self):
        value = self._client.state[self._zone]["source"]
        return value if value in self.options else None

    async def async_select_option(self, option: str):
        await self._client.set_source(self._zone, option)
        self.async_write_ha_state()

    def _on_zone_update(self, zone):
        if zone == self._zone:
            self.async_write_ha_state()
