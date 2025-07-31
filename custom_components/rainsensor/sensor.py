"""Sensor platform for Rain Sensor."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import DOMAIN, RainSensorDataHandler


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the Rain Sensor sensor platform."""
    # Retrieve the data handler for this config entry.
    data_handler: RainSensorDataHandler = hass.data[DOMAIN][entry.entry_id]

    # Create all sensor entities that represent different aspects of the rain data (counts, rainfall, rate).
    daily_on_entity = DailyOnCountSensorEntity(data_handler)
    daily_off_entity = DailyOffCountSensorEntity(data_handler)
    total_on_entity = TotalOnCountSensorEntity(data_handler)
    total_off_entity = TotalOffCountSensorEntity(data_handler)
    daily_rain_entity = DailyRainSensorEntity(data_handler)
    total_rain_entity = TotalRainSensorEntity(data_handler)
    daily_tilt_entity = DailyTiltSensorEntity(data_handler)
    total_tilt_entity = TotalTiltSensorEntity(data_handler)
    rate_entity = RainfallRateSensorEntity(data_handler)

    # Assign entities back to the data handler so it can update them directly when state changes.
    data_handler.daily_on_entity = daily_on_entity
    data_handler.daily_off_entity = daily_off_entity
    data_handler.total_on_entity = total_on_entity
    data_handler.total_off_entity = total_off_entity
    data_handler.daily_rain_entity = daily_rain_entity
    data_handler.total_rain_entity = total_rain_entity
    data_handler.daily_tilt_entity = daily_tilt_entity
    data_handler.total_tilt_entity = total_tilt_entity
    data_handler.rate_entity = rate_entity

    # Add all entities to Home Assistant.
    async_add_entities([
        daily_on_entity,
        daily_off_entity,
        total_on_entity,
        total_off_entity,
        daily_rain_entity,
        total_rain_entity,
        daily_tilt_entity,
        total_tilt_entity,
        rate_entity,
    ])


class DailyOnCountSensorEntity(SensorEntity, RestoreEntity):
    """Representation of a daily on count sensor entity."""

    # Disable polling since updates are pushed via the data handler.
    _attr_should_poll = False
    _attr_native_unit_of_measurement = "counts"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the daily on count sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_daily_on_count"
        self._attr_name = f"{data_handler.name} Daily On Count"
        # Group all sensors under one device in the UI for better organization.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state for daily on count if same day."""
        await super().async_added_to_hass()
        # Retrieve last known state to restore count, but only if it's from the same day to avoid carrying over old data.
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            None,
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            try:
                count = int(float(last_state.state))
            except ValueError:
                count = 0
            tz = dt_util.get_time_zone(self.hass.config.time_zone)
            last_updated_date = last_state.last_updated.astimezone(tz).date()
            current_date = dt_util.now().date()
            self._data_handler._flips_on = count if last_updated_date == current_date else 0
        else:
            self._data_handler._flips_on = 0
        # Update the state after restoration.
        self._data_handler.update_state()

    @property
    def native_value(self) -> int | None:
        """Return the native value of the daily on count sensor."""
        return self._data_handler._flips_on


class DailyOffCountSensorEntity(SensorEntity, RestoreEntity):
    """Representation of a daily off count sensor entity."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "counts"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the daily off count sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_daily_off_count"
        self._attr_name = f"{data_handler.name} Daily Off Count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state for daily off count if same day."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            None,
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            try:
                count = int(float(last_state.state))
            except ValueError:
                count = 0
            tz = dt_util.get_time_zone(self.hass.config.time_zone)
            last_updated_date = last_state.last_updated.astimezone(tz).date()
            current_date = dt_util.now().date()
            self._data_handler._flips_off = count if last_updated_date == current_date else 0
        else:
            self._data_handler._flips_off = 0
        self._data_handler.update_state()

    @property
    def native_value(self) -> int | None:
        """Return the native value of the daily off count sensor."""
        return self._data_handler._flips_off


class TotalOnCountSensorEntity(SensorEntity, RestoreEntity):
    """Representation of a total on count sensor entity."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "counts"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the total on count sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_total_on_count"
        self._attr_name = f"{data_handler.name} Total On Count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state for total on count."""
        await super().async_added_to_hass()
        # Restore the total count without day check, as totals are cumulative across restarts.
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            None,
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            try:
                self._data_handler._total_flips_on = int(float(last_state.state))
            except ValueError:
                self._data_handler._total_flips_on = 0
        else:
            self._data_handler._total_flips_on = 0
        self._data_handler.update_state()

    @property
    def native_value(self) -> int | None:
        """Return the native value of the total on count sensor."""
        return self._data_handler._total_flips_on


class TotalOffCountSensorEntity(SensorEntity, RestoreEntity):
    """Representation of a total off count sensor entity."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "counts"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the total off count sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_total_off_count"
        self._attr_name = f"{data_handler.name} Total Off Count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last state for total off count."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            None,
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            try:
                self._data_handler._total_flips_off = int(float(last_state.state))
            except ValueError:
                self._data_handler._total_flips_off = 0
        else:
            self._data_handler._total_flips_off = 0
        self._data_handler.update_state()

    @property
    def native_value(self) -> int | None:
        """Return the native value of the total off count sensor."""
        return self._data_handler._total_flips_off


class DailyRainSensorEntity(SensorEntity):
    """Representation of a daily rain sensor entity."""

    _attr_should_poll = False
    _attr_suggested_display_precision = 1

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the daily rain sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_daily"
        self._attr_name = f"{data_handler.name} Daily"
        self._attr_native_unit_of_measurement = data_handler.unit_of_measurement
        self._attr_icon = data_handler.icon
        self._attr_device_class = data_handler.device_class
        self._attr_state_class = data_handler.state_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the daily rain sensor."""
        return self._data_handler.state


class TotalRainSensorEntity(SensorEntity):
    """Representation of a total rain sensor entity."""

    _attr_should_poll = False
    _attr_suggested_display_precision = 1

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the total rain sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_total"
        self._attr_name = f"{data_handler.name} Total"
        self._attr_native_unit_of_measurement = data_handler.unit_of_measurement
        self._attr_icon = data_handler.icon
        self._attr_device_class = data_handler.device_class
        # Use TOTAL_INCREASING for totals that only go up.
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the total rain sensor."""
        return self._data_handler.total_state


class DailyTiltSensorEntity(SensorEntity):
    """Representation of a daily tilt count sensor entity."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "tips"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the daily tilt sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_daily_tilt"
        self._attr_name = f"{data_handler.name} Daily Tilt Count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    @property
    def native_value(self) -> int | None:
        """Return the native value of the daily tilt sensor."""
        return self._data_handler.daily_tilt_count


class TotalTiltSensorEntity(SensorEntity):
    """Representation of a total tilt count sensor entity."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "tips"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the total tilt sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_total_tilt"
        self._attr_name = f"{data_handler.name} Total Tilt Count"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    @property
    def native_value(self) -> int | None:
        """Return the native value of the total tilt sensor."""
        return self._data_handler.total_tilt_count


class RainfallRateSensorEntity(SensorEntity):
    """Representation of a rainfall rate sensor entity."""

    _attr_should_poll = False
    _attr_native_unit_of_measurement = "mm/h"
    _attr_icon = "mdi:weather-rainy"
    _attr_device_class = SensorDeviceClass.PRECIPITATION_INTENSITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, data_handler: RainSensorDataHandler) -> None:
        """Initialize the rainfall rate sensor entity."""
        self._data_handler = data_handler
        self._attr_unique_id = f"{data_handler.unique_id}_rate"
        self._attr_name = f"{data_handler.name} Rainfall Rate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data_handler.unique_id)},
            name=data_handler.name,
        )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the rainfall rate sensor."""
        return self._data_handler.rate
