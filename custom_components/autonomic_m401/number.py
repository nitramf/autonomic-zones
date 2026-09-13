from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client = entry.runtime_data
    names = entry.data["zone_names"]
    async_add_entities([
        AutonomicVolume(client, zone, names[i])
        for i, zone in enumerate(client.zones)
    ])

class AutonomicVolume(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:volume-high"

    def __init__(self, client, zone, room_name):
        self._client = client
        self._zone = zone
        self._attr_name = "Volume"
        self._attr_unique_id = f"autonomic_m401_zone_{zone}_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"zone_{zone}")},
            "name": f"Autonomic M401 – {room_name}",
            "manufacturer": "Autonomic",
            "model": "M401",
        }
        self._client.add_listener(self._on_zone_update)

    @property
    def native_value(self):
        return self._client.state[self._zone]["volume"]

    async def async_set_native_value(self, value: float):
        await self._client.set_volume(self._zone, int(value))
        self.async_write_ha_state()

    def _on_zone_update(self, zone):
        if zone == self._zone:
            self.async_write_ha_state()
