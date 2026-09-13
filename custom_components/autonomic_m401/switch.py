from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client = entry.runtime_data
    names = entry.data["zone_names"]
    entities = [
        AutonomicPowerSwitch(client, zone, names[i])
        for i, zone in enumerate(client.zones)
    ]
    async_add_entities(entities)

class AutonomicPowerSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:speaker-wireless"

    def __init__(self, client, zone, room_name):
        self._client = client
        self._zone = zone
        self._attr_name = "Power"
        self._attr_unique_id = f"autonomic_m401_zone_{zone}_power"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"zone_{zone}")},
            "name": f"Autonomic M401 – {room_name}",
            "manufacturer": "Autonomic",
            "model": "M401",
        }
        self._client.add_listener(self._on_zone_update)

    @property
    def is_on(self):
        return self._client.state[self._zone]["power"]

    async def async_turn_on(self, **kwargs):
        await self._client.set_power(self._zone, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._client.set_power(self._zone, False)
        self.async_write_ha_state()

    def _on_zone_update(self, zone):
        if zone == self._zone:
            self.async_write_ha_state()
