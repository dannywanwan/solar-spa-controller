"""Switch platform for Solar Spa Controller."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarSpaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Spa Controller switch."""
    coordinator: SolarSpaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolarSpaControllerSwitch(coordinator, entry)])


class SolarSpaControllerSwitch(
    CoordinatorEntity[SolarSpaCoordinator],
    RestoreEntity,
    SwitchEntity,
):
    """Switch that enables or disables automatic spa control."""

    _attr_has_entity_name = True
    _attr_translation_key = "automatic_control"
    _attr_icon = "mdi:spa"

    def __init__(self, coordinator: SolarSpaCoordinator, entry: ConfigEntry) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_automatic_control"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Solar Spa Controller",
        }

    async def async_added_to_hass(self) -> None:
        """Restore the previous switch state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.coordinator.controller_enabled = last_state.state == "on"

    @property
    def is_on(self) -> bool:
        """Return whether automatic control is enabled."""
        return self.coordinator.controller_enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Enable automatic spa control."""
        await self.coordinator.async_set_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable automatic spa control."""
        await self.coordinator.async_set_enabled(False)

