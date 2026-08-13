"""Constants for Solar Spa Controller."""

DOMAIN = "solar_spa_controller"

CONF_SOLAR_ENTITY = "solar_entity"
CONF_POWER_SOURCE = "power_source"
CONF_CT_EXPORT_SIGN = "ct_export_sign"
CONF_SPA_CLIMATE_ENTITY = "spa_climate_entity"
CONF_HEAT_TEMPERATURE = "heat_temperature"
CONF_COOL_TEMPERATURE = "cool_temperature"
CONF_ON_THRESHOLD = "on_threshold"
CONF_OFF_THRESHOLD = "off_threshold"
CONF_AVERAGING_WINDOW = "averaging_window"
CONF_MIN_HOLD_TIME = "min_hold_time"
CONF_SAMPLING_INTERVAL = "sampling_interval"

DEFAULT_HEAT_TEMPERATURE = 38.0
DEFAULT_COOL_TEMPERATURE = 26.0
DEFAULT_ON_THRESHOLD = 3800
DEFAULT_OFF_THRESHOLD = 3200
DEFAULT_AVERAGING_WINDOW = 10
DEFAULT_MIN_HOLD_TIME = 5
DEFAULT_SAMPLING_INTERVAL = 60
DEFAULT_POWER_SOURCE = "solar_panels"
DEFAULT_CT_EXPORT_SIGN = "positive_export"

POWER_SOURCE_SOLAR_PANELS = "solar_panels"
POWER_SOURCE_CT_CLAMPS = "ct_clamps"

CT_EXPORT_POSITIVE = "positive_export"
CT_EXPORT_NEGATIVE = "negative_export"

STATE_HEATING = "heating"
STATE_COOLING = "cooling"
STATE_WAITING = "waiting"
STATE_WARMING_UP = "warming_up"
STATE_INACTIVE = "inactive"
