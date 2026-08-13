# Solar Spa Controller

![Solar Spa Controller icon](brand/icon.png)

Solar Spa Controller is a Home Assistant custom integration that watches available solar power and adjusts a spa climate entity's target temperature based on averaged output.

It is designed to replace a fragile automation with a small controller that has:

- UI setup from **Settings > Devices & services**
- Power source selection for solar panel production or CT clamps
- Power sensor entity selection
- Spa climate entity selection
- Heat and cool target temperatures
- Separate solar ON and OFF thresholds for hysteresis
- Configurable averaging window, sampling interval, and minimum hold time
- Diagnostic sensors for average solar power and controller state

## Installation

1. Copy `custom_components/solar_spa_controller` into your Home Assistant `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration**.
4. Search for **Solar Spa Controller**.
5. Select whether the power data comes from your solar panels or CT clamps.
6. Select the matching power sensor and spa climate entity, then set the thresholds and temperatures.

## Recommended Starting Settings

A reasonable first pass for many spa setups:

- Averaging window: `10` minutes
- Solar ON threshold: `3800` W
- Solar OFF threshold: `3200` W
- Minimum hold time: `5` minutes
- Sampling interval: `60` seconds

Tune these after watching the diagnostic entities for a day or two.

## How It Works

The integration samples the selected power sensor on a schedule and keeps a rolling average. If the average available power rises above the ON threshold, it sets the spa climate entity to the configured heat target. If the average drops below the OFF threshold, it sets the spa to the configured cool target.

The two thresholds prevent rapid switching when solar production hovers around one number. The minimum hold time adds another guard against frequent setpoint changes during patchy cloud.

If the selected sensor reports in `kW`, values are automatically converted to watts.

For CT clamps, you can choose whether export/available power is reported as a positive or negative value. If your clamp sensor reports grid import as positive and grid export as negative, choose the negative export option.

## Notes

"Cool" means lowering the spa climate entity's target temperature with `climate.set_temperature`. The integration does not attempt to switch the spa into an HVAC cooling mode.

## Entities

The integration creates:

- **Average available power** sensor
- **Controller state** diagnostic sensor

The controller state includes the current decision and the last action taken.
