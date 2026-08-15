"""Coordinator for Solar Spa Controller."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil
import logging

from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, UnitOfPower
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_AVERAGING_WINDOW,
    CONF_COOL_TEMPERATURE,
    CONF_COOL_SCENE_ENTITY,
    CONF_CT_EXPORT_SIGN,
    CONF_HEAT_TEMPERATURE,
    CONF_HEAT_SCENE_ENTITY,
    CONF_HIGH_RANGE_OPTION,
    CONF_LOW_RANGE_OPTION,
    CONF_MIN_HOLD_TIME,
    CONF_OFF_THRESHOLD,
    CONF_ON_THRESHOLD,
    CONF_POWER_SOURCE,
    CONF_SAMPLING_INTERVAL,
    CONF_SOLAR_ENTITY,
    CONF_SPA_CLIMATE_ENTITY,
    CONF_TEMP_RANGE_SELECT_ENTITY,
    CT_EXPORT_NEGATIVE,
    DEFAULT_CT_EXPORT_SIGN,
    DEFAULT_AVERAGING_WINDOW,
    DEFAULT_COOL_TEMPERATURE,
    DEFAULT_HEAT_TEMPERATURE,
    DEFAULT_HIGH_RANGE_OPTION,
    DEFAULT_LOW_RANGE_OPTION,
    DEFAULT_MIN_HOLD_TIME,
    DEFAULT_OFF_THRESHOLD,
    DEFAULT_ON_THRESHOLD,
    DEFAULT_POWER_SOURCE,
    DEFAULT_SAMPLING_INTERVAL,
    DOMAIN,
    POWER_SOURCE_CT_CLAMPS,
    STATE_COOLING,
    STATE_HEATING,
    STATE_INACTIVE,
    STATE_WAITING,
    STATE_WARMING_UP,
)

_LOGGER = logging.getLogger(__name__)
SERVICE_SET_TEMPERATURE = "set_temperature"
SERVICE_SELECT_OPTION = "select_option"
SERVICE_TURN_ON = "turn_on"


@dataclass(slots=True)
class SolarSpaData:
    """Runtime data exposed by sensor entities."""

    average_power: float | None
    controller_state: str
    last_action: str
    sample_count: int
    active_target: str | None
    controller_enabled: bool


class SolarSpaCoordinator(DataUpdateCoordinator[SolarSpaData]):
    """Track solar production and adjust the spa setpoint."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self._samples: deque[tuple[datetime, float]] = deque()
        self._active_target: str | None = None
        self._last_switch: datetime | None = None
        self._last_action = "Controller initialized"
        self.controller_enabled = True

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._option(CONF_SAMPLING_INTERVAL)),
        )

    async def _async_update_data(self) -> SolarSpaData:
        """Sample solar production and update the spa target when needed."""
        try:
            now = dt_util.utcnow()
            power = self._read_available_power()
            if power is not None:
                self._samples.append((now, power))
            self._trim_samples(now)

            average = self._average_power()
            state = await self._maybe_control_spa(now, average)

            return SolarSpaData(
                average_power=average,
                controller_state=state,
                last_action=self._last_action,
                sample_count=len(self._samples),
                active_target=self._active_target,
                controller_enabled=self.controller_enabled,
            )
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic spa control."""
        self.controller_enabled = enabled
        self._last_action = (
            "Automatic spa control enabled"
            if enabled
            else "Automatic spa control disabled; monitoring only"
        )
        await self.async_request_refresh()

    def _read_available_power(self) -> float | None:
        """Read the selected power entity and normalize to available watts."""
        state = self.hass.states.get(self._option(CONF_SOLAR_ENTITY))
        if state is None or state.state in {"unknown", "unavailable"}:
            self._last_action = "Power source sensor unavailable"
            return None

        try:
            value = float(state.state)
        except ValueError:
            self._last_action = f"Power source sensor value is not numeric: {state.state}"
            return None

        if _state_unit(state) == UnitOfPower.KILO_WATT:
            value *= 1000

        if (
            self._option(CONF_POWER_SOURCE) == POWER_SOURCE_CT_CLAMPS
            and self._option(CONF_CT_EXPORT_SIGN) == CT_EXPORT_NEGATIVE
        ):
            return -value

        return value

    def _trim_samples(self, now: datetime) -> None:
        """Keep samples inside the configured averaging window."""
        cutoff = now - timedelta(minutes=self._option(CONF_AVERAGING_WINDOW))
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _average_power(self) -> float | None:
        """Return the rolling average solar power in watts."""
        if not self._samples:
            return None
        return sum(sample for _, sample in self._samples) / len(self._samples)

    async def _maybe_control_spa(
        self,
        now: datetime,
        average: float | None,
    ) -> str:
        """Apply threshold logic and set the spa target when needed."""
        if average is None:
            return STATE_WAITING

        if not self.controller_enabled:
            self._last_action = (
                f"Automatic spa control is off; average available power is "
                f"{average:.0f} W"
            )
            return STATE_INACTIVE

        on_threshold = self._option(CONF_ON_THRESHOLD)
        off_threshold = self._option(CONF_OFF_THRESHOLD)

        desired_target: str | None = None
        desired_temperature: float | None = None

        if average >= on_threshold:
            desired_target = STATE_HEATING
            desired_temperature = self._option(CONF_HEAT_TEMPERATURE)
        elif average <= off_threshold:
            desired_target = STATE_COOLING
            desired_temperature = self._option(CONF_COOL_TEMPERATURE)

        if desired_target == STATE_HEATING and not self._averaging_window_ready(now):
            required_samples = self._required_sample_count()
            self._last_action = (
                f"Warming up before heating; average available power is "
                f"{average:.0f} W from {len(self._samples)} of "
                f"{required_samples} required sample(s)"
            )
            return self._active_target or STATE_WARMING_UP

        if desired_target is None:
            self._last_action = (
                f"Average available power is {average:.0f} W, between thresholds; "
                "holding state"
            )
            return self._active_target or STATE_WAITING

        if desired_target == self._active_target:
            self._last_action = (
                f"Already {desired_target}; average available power is {average:.0f} W"
            )
            return desired_target

        if not self._hold_time_elapsed(now):
            self._last_action = (
                f"Waiting for hold time before switching to {desired_target}; "
                f"average available power is {average:.0f} W"
            )
            return self._active_target or STATE_WAITING

        try:
            scene_result = await self._async_activate_scene(desired_target, average)
            if scene_result is True:
                self._active_target = desired_target
                self._last_switch = now
                return desired_target
            if scene_result is None:
                return self._active_target or STATE_WAITING

            range_ok = await self._async_set_temperature_range(desired_target)
            if not range_ok:
                return self._active_target or STATE_WAITING

            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {
                    ATTR_ENTITY_ID: self._option(CONF_SPA_CLIMATE_ENTITY),
                    ATTR_TEMPERATURE: desired_temperature,
                },
                blocking=True,
            )
        except Exception as err:
            self._last_action = (
                f"Could not set spa temperature to {desired_temperature:g} C: {err}"
            )
            _LOGGER.warning(
                "Could not set spa temperature for %s",
                self._option(CONF_SPA_CLIMATE_ENTITY),
                exc_info=True,
            )
            return self._active_target or STATE_WAITING

        self._active_target = desired_target
        self._last_switch = now
        self._last_action = (
            f"Set spa to {desired_temperature:g} C because average available power "
            f"was {average:.0f} W"
        )
        return desired_target

    async def _async_activate_scene(
        self,
        desired_target: str,
        average: float,
    ) -> bool | None:
        """Activate a configured scene for the desired target."""
        scene_entity = (
            self._option(CONF_HEAT_SCENE_ENTITY)
            if desired_target == STATE_HEATING
            else self._option(CONF_COOL_SCENE_ENTITY)
        )
        if not scene_entity:
            return False

        try:
            await self.hass.services.async_call(
                "scene",
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: scene_entity},
                blocking=True,
            )
        except Exception as err:
            self._last_action = f"Could not activate scene {scene_entity}: {err}"
            _LOGGER.warning(
                "Could not activate scene %s",
                scene_entity,
                exc_info=True,
            )
            return None

        self._last_action = (
            f"Activated {scene_entity} because average available power was "
            f"{average:.0f} W"
        )
        return True

    async def _async_set_temperature_range(self, desired_target: str) -> bool:
        """Switch a separate spa range select entity before setting temperature."""
        range_entity = self._option(CONF_TEMP_RANGE_SELECT_ENTITY)
        if not range_entity:
            return True

        option = (
            self._option(CONF_HIGH_RANGE_OPTION)
            if desired_target == STATE_HEATING
            else self._option(CONF_LOW_RANGE_OPTION)
        )
        if not option:
            return True

        try:
            await self.hass.services.async_call(
                "select",
                SERVICE_SELECT_OPTION,
                {
                    ATTR_ENTITY_ID: range_entity,
                    "option": option,
                },
                blocking=True,
            )
        except Exception as err:
            self._last_action = (
                f"Could not set spa temperature range to {option}: {err}"
            )
            _LOGGER.warning(
                "Could not set spa temperature range for %s to %s",
                range_entity,
                option,
                exc_info=True,
            )
            return False

        return True

    def _hold_time_elapsed(self, now: datetime) -> bool:
        """Return whether enough time has passed since the last switch."""
        if self._last_switch is None:
            return True

        hold_time = timedelta(minutes=self._option(CONF_MIN_HOLD_TIME))
        return now - self._last_switch >= hold_time

    def _averaging_window_ready(self, now: datetime) -> bool:
        """Return whether the controller has enough samples to act."""
        return len(self._samples) >= self._required_sample_count()

    def _required_sample_count(self) -> int:
        """Return the sample count needed for the configured averaging window."""
        window_seconds = self._option(CONF_AVERAGING_WINDOW) * 60
        sampling_interval = self._option(CONF_SAMPLING_INTERVAL)
        return max(1, ceil(window_seconds / sampling_interval))

    def _option(self, key: str):
        """Read an option, falling back to config data and defaults."""
        defaults = {
            CONF_HEAT_TEMPERATURE: DEFAULT_HEAT_TEMPERATURE,
            CONF_COOL_TEMPERATURE: DEFAULT_COOL_TEMPERATURE,
            CONF_POWER_SOURCE: DEFAULT_POWER_SOURCE,
            CONF_CT_EXPORT_SIGN: DEFAULT_CT_EXPORT_SIGN,
            CONF_HEAT_SCENE_ENTITY: None,
            CONF_COOL_SCENE_ENTITY: None,
            CONF_TEMP_RANGE_SELECT_ENTITY: None,
            CONF_LOW_RANGE_OPTION: DEFAULT_LOW_RANGE_OPTION,
            CONF_HIGH_RANGE_OPTION: DEFAULT_HIGH_RANGE_OPTION,
            CONF_ON_THRESHOLD: DEFAULT_ON_THRESHOLD,
            CONF_OFF_THRESHOLD: DEFAULT_OFF_THRESHOLD,
            CONF_AVERAGING_WINDOW: DEFAULT_AVERAGING_WINDOW,
            CONF_MIN_HOLD_TIME: DEFAULT_MIN_HOLD_TIME,
            CONF_SAMPLING_INTERVAL: DEFAULT_SAMPLING_INTERVAL,
        }
        return self.entry.options.get(key, self.entry.data.get(key, defaults.get(key)))


def _state_unit(state: State) -> str | None:
    """Return a state's unit of measurement."""
    return state.attributes.get("unit_of_measurement")
