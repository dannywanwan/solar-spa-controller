"""Sensor platform for Solar Spa Controller."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarSpaCoordinator


SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="average_power",
        translation_key="average_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="controller_state",
        translation_key="controller_state",
        icon="mdi:spa",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Spa Controller sensors."""
    coordinator: SolarSpaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SolarSpaSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SolarSpaSensor(CoordinatorEntity[SolarSpaCoordinator], SensorEntity):
    """Representation of a Solar Spa Controller sensor."""

    entity_description: SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarSpaCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Solar Spa Controller",
        }

    @property
    def native_value(self):
        """Return the sensor value."""
        data = self.coordinator.data
        if data is None:
            return None

        if self.entity_description.key == "average_power":
            if data.average_power is None:
                return None
            return round(data.average_power, 1)

        if self.entity_description.key == "controller_state":
            return data.controller_state

        return None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return diagnostic attributes."""
        data = self.coordinator.data
        if data is None:
            return None

        return {
            "last_action": data.last_action,
            "sample_count": data.sample_count,
            "active_target": data.active_target,
        }

