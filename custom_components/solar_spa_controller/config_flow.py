"""Config flow for Solar Spa Controller."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers import selector

from .const import (
    CONF_AVERAGING_WINDOW,
    CONF_COOL_TEMPERATURE,
    CONF_CT_EXPORT_SIGN,
    CONF_HEAT_TEMPERATURE,
    CONF_MIN_HOLD_TIME,
    CONF_OFF_THRESHOLD,
    CONF_ON_THRESHOLD,
    CONF_POWER_SOURCE,
    CONF_SAMPLING_INTERVAL,
    CONF_SOLAR_ENTITY,
    CONF_SPA_CLIMATE_ENTITY,
    CT_EXPORT_NEGATIVE,
    CT_EXPORT_POSITIVE,
    DEFAULT_AVERAGING_WINDOW,
    DEFAULT_COOL_TEMPERATURE,
    DEFAULT_CT_EXPORT_SIGN,
    DEFAULT_HEAT_TEMPERATURE,
    DEFAULT_MIN_HOLD_TIME,
    DEFAULT_OFF_THRESHOLD,
    DEFAULT_ON_THRESHOLD,
    DEFAULT_POWER_SOURCE,
    DEFAULT_SAMPLING_INTERVAL,
    DOMAIN,
    POWER_SOURCE_CT_CLAMPS,
    POWER_SOURCE_SOLAR_PANELS,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the user-facing config schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_POWER_SOURCE,
                default=defaults.get(CONF_POWER_SOURCE, DEFAULT_POWER_SOURCE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=POWER_SOURCE_SOLAR_PANELS,
                            label="Solar panels",
                        ),
                        selector.SelectOptionDict(
                            value=POWER_SOURCE_CT_CLAMPS,
                            label="CT clamps",
                        ),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_SOLAR_ENTITY,
                default=defaults.get(CONF_SOLAR_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Required(
                CONF_CT_EXPORT_SIGN,
                default=defaults.get(CONF_CT_EXPORT_SIGN, DEFAULT_CT_EXPORT_SIGN),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=CT_EXPORT_POSITIVE,
                            label="Positive value means export/available power",
                        ),
                        selector.SelectOptionDict(
                            value=CT_EXPORT_NEGATIVE,
                            label="Negative value means export/available power",
                        ),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_SPA_CLIMATE_ENTITY,
                default=defaults.get(CONF_SPA_CLIMATE_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["climate"])
            ),
            vol.Required(
                CONF_HEAT_TEMPERATURE,
                default=defaults.get(CONF_HEAT_TEMPERATURE, DEFAULT_HEAT_TEMPERATURE),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=45,
                    step=0.5,
                    unit_of_measurement=UnitOfTemperature.CELSIUS,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_COOL_TEMPERATURE,
                default=defaults.get(CONF_COOL_TEMPERATURE, DEFAULT_COOL_TEMPERATURE),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=45,
                    step=0.5,
                    unit_of_measurement=UnitOfTemperature.CELSIUS,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_ON_THRESHOLD,
                default=defaults.get(CONF_ON_THRESHOLD, DEFAULT_ON_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=20000,
                    step=100,
                    unit_of_measurement="W",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_OFF_THRESHOLD,
                default=defaults.get(CONF_OFF_THRESHOLD, DEFAULT_OFF_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=20000,
                    step=100,
                    unit_of_measurement="W",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_AVERAGING_WINDOW,
                default=defaults.get(CONF_AVERAGING_WINDOW, DEFAULT_AVERAGING_WINDOW),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=120,
                    step=1,
                    unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_MIN_HOLD_TIME,
                default=defaults.get(CONF_MIN_HOLD_TIME, DEFAULT_MIN_HOLD_TIME),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=120,
                    step=1,
                    unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SAMPLING_INTERVAL,
                default=defaults.get(CONF_SAMPLING_INTERVAL, DEFAULT_SAMPLING_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=10,
                    max=900,
                    step=10,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


class SolarSpaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Solar Spa Controller config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                await self.async_set_unique_id(
                    f"{user_input[CONF_SOLAR_ENTITY]}_{user_input[CONF_SPA_CLIMATE_ENTITY]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Solar Spa Controller",
                    data=user_input,
                )

            return self.async_show_form(
                step_id="user",
                data_schema=_schema(user_input),
                errors=errors,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema({}),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SolarSpaOptionsFlow(config_entry)


class SolarSpaOptionsFlow(config_entries.OptionsFlow):
    """Handle Solar Spa Controller options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        defaults = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

            return self.async_show_form(
                step_id="init",
                data_schema=_schema(user_input),
                errors=errors,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(defaults),
        )


def _validate(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate threshold relationships."""
    errors: dict[str, str] = {}
    if user_input[CONF_OFF_THRESHOLD] >= user_input[CONF_ON_THRESHOLD]:
        errors["base"] = "off_threshold_must_be_below_on_threshold"
    if user_input[CONF_COOL_TEMPERATURE] >= user_input[CONF_HEAT_TEMPERATURE]:
        errors["base"] = "cool_temperature_must_be_below_heat_temperature"
    return errors
