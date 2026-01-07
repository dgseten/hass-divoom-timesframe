from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import DivoomClient
from .const import DOMAIN, MANUFACTURER, MODEL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: DivoomClient = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, "Divoom Time Frame")
    async_add_entities(
        [DivoomBrightnessNumber(hass, entry, client, name)],
        update_before_add=False,
    )


@dataclass
class _OptimisticBrightness:
    value: int = 100


class DivoomBrightnessNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_icon = "mdi:brightness-6"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: DivoomClient,
        device_name: str,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._client = client
        self._device_name = device_name
        self._state = _OptimisticBrightness()

        self._attr_unique_id = f"{entry.unique_id}_brightness"
        self._attr_name = "Brightness"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> int:
        return self._state.value

    async def async_set_native_value(self, value: float) -> None:
        session = async_get_clientsession(self.hass)
        await self._client.set_brightness(session, int(value))
        self._state.value = int(value)
        self.async_write_ha_state()
