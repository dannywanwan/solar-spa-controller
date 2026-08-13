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
- Automatic control switch so you can pause solar-based setpoint changes
- Diagnostic sensors for average solar power and controller state

## Installation

### HACS

1. Add `https://github.com/dannywanwan/solar-spa-controller` as a HACS custom repository with category **Integration**.
2. Install **Solar Spa Controller** from HACS.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration**.
5. Search for **Solar Spa Controller**.
6. Select whether the power data comes from your solar panels or CT clamps.
7. Select the matching power sensor and spa climate entity, then set the thresholds and temperatures.

HACS installs the files only. The entities and device are created after the integration is added through **Devices & services**.

### Updating

After updating Solar Spa Controller through HACS, restart Home Assistant. HACS updates the files on disk, but Home Assistant may keep the old custom integration code loaded until a full restart.

### Manual

1. Copy `custom_components/solar_spa_controller` into your Home Assistant `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Add **Solar Spa Controller** from **Settings > Devices & services > Add integration**.

## Recommended Starting Settings

A reasonable first pass for many spa setups:

- Heat target: `38` C
- Cool target: `26` C
- Averaging window: `10` minutes
- Solar ON threshold: `3800` W
- Solar OFF threshold: `3200` W
- Minimum hold time: `5` minutes
- Sampling interval: `60` seconds

The setup UI limits the low/cool target to `18-26` C and the high/heat target to `26-40` C.

Tune these after watching the diagnostic entities for a day or two.

## How It Works

The integration samples the selected power sensor on a schedule and keeps a rolling average. If the average available power rises above the ON threshold, it sets the spa climate entity to the configured heat target. If the average drops below the OFF threshold, it sets the spa to the configured cool target.

The two thresholds prevent rapid switching when solar production hovers around one number. The minimum hold time adds another guard against frequent setpoint changes during patchy cloud.

If the selected sensor reports in `kW`, values are automatically converted to watts.

For CT clamps, you can choose whether export/available power is reported as a positive or negative value. If your clamp sensor reports grid import as positive and grid export as negative, choose the negative export option.

Turn **Automatic control** off when you want to heat the spa manually. The integration will keep monitoring available power and updating its diagnostic entities, but it will not change the spa's target temperature while the switch is off.

## Notes

"Cool" means lowering the spa climate entity's target temperature with `climate.set_temperature`. The integration does not attempt to switch the spa into an HVAC cooling mode.

## Entities

The integration creates:

- **Average available power** sensor
- **Controller state** diagnostic sensor
- **Automatic control** switch

The controller state includes the current decision and the last action taken.
