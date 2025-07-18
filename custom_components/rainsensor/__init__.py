"""Rain Sensor Integration."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.components.recorder import history
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from .sensor import (
        DailyOffCountSensorEntity,
        DailyOnCountSensorEntity,
        DailyRainSensorEntity,
        DailyTiltSensorEntity,
        RainfallRateSensorEntity,
        TotalOffCountSensorEntity,
        TotalOnCountSensorEntity,
        TotalRainSensorEntity,
        TotalTiltSensorEntity,
    )

DOMAIN = "rainsensor"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rain Sensor from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    conf = {**entry.data, **entry.options}

    data_handler = RainSensorDataHandler(
        hass,
        conf[CONF_ENTITY_ID],
        conf["volume_per_tilt_on"],
        conf["volume_per_tilt_off"],
        conf["funnel_diameter"],
        conf[CONF_NAME],
        entry.unique_id,
        conf.get("enable_missed_flip_recovery", False),
    )

    hass.data[DOMAIN][entry.entry_id] = data_handler

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    data_handler.remove_state_listener = async_track_state_change_event(
        hass, conf[CONF_ENTITY_ID], data_handler.handle_state_change
    )

    await data_handler.restore_tip_history()

    data_handler.schedule_midnight_reset()
    data_handler.schedule_rate_update()

    entry.async_on_unload(data_handler.async_unload)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            data_handler: RainSensorDataHandler = hass.data[DOMAIN].pop(entry.entry_id)
            data_handler.unload()
    return unload_ok


class RainSensorDataHandler:
    """Handles data and logic for the Rain Sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str,
        volume_per_tilt_on: float,
        volume_per_tilt_off: float,
        funnel_diameter: float,
        name: str,
        unique_id: str,
        enable_missed_flip_recovery: bool,
    ) -> None:
        """Initialize the data handler."""
        self._hass = hass
        self._entity_id = entity_id
        self._volume_per_tilt_on = volume_per_tilt_on
        self._volume_per_tilt_off = volume_per_tilt_off
        self._funnel_diameter = funnel_diameter
        self._name = name
        self._unique_id = unique_id
        self._enable_missed_flip_recovery = enable_missed_flip_recovery
        self._flips_on: int = 0
        self._flips_off: int = 0
        self._total_flips_on: int = 0
        self._total_flips_off: int = 0
        self._state: float = 0.0  # Daily rainfall in mm
        self._total_state: float = 0.0  # Total rainfall in mm
        self._rate: float = 0.0  # Rainfall rate in mm/h
        self._tip_history: deque[tuple[datetime, float]] = deque()  # (time, volume_ml)

        # Precompute conversion factor: rain depth in mm = (volume_ml * 1000) / area_mm²
        funnel_area_mm2 = (funnel_diameter / 2.0) ** 2 * 3.141592653589793
        self._factor_per_ml = 1000.0 / funnel_area_mm2 if funnel_area_mm2 > 0 else 0.0

        self.daily_on_entity: DailyOnCountSensorEntity | None = None
        self.daily_off_entity: DailyOffCountSensorEntity | None = None
        self.total_on_entity: TotalOnCountSensorEntity | None = None
        self.total_off_entity: TotalOffCountSensorEntity | None = None
        self.daily_rain_entity: DailyRainSensorEntity | None = None
        self.total_rain_entity: TotalRainSensorEntity | None = None
        self.daily_tilt_entity: DailyTiltSensorEntity | None = None
        self.total_tilt_entity: TotalTiltSensorEntity | None = None
        self.rate_entity: RainfallRateSensorEntity | None = None
        self.remove_state_listener: callback | None = None
        self._remove_midnight_reset: callback | None = None
        self._remove_rate_update: callback | None = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID."""
        return self._unique_id

    @property
    def state(self) -> float:
        """Return the daily rainfall in mm."""
        return self._state

    @property
    def total_state(self) -> float:
        """Return the total rainfall in mm."""
        return self._total_state

    @property
    def rate(self) -> float:
        """Return the rainfall rate in mm/h."""
        return self._rate

    @property
    def daily_tilt_count(self) -> int:
        """Return the daily tilt count."""
        return self._flips_on + self._flips_off

    @property
    def total_tilt_count(self) -> int:
        """Return the total tilt count."""
        return self._total_flips_on + self._total_flips_off

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement for rainfall."""
        return "mm"

    @property
    def icon(self) -> str:
        """Return the icon for rainfall sensors."""
        return "mdi:weather-pouring"

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return the device class for rainfall."""
        return SensorDeviceClass.PRECIPITATION

    @property
    def state_class(self) -> SensorStateClass:
        """Return the state class for rainfall."""
        return SensorStateClass.TOTAL

    @callback
    def handle_state_change(self, event: EventStateChangedData) -> None:
        """Handle state changes of the monitored binary sensor."""
        old_state_obj = event.data.get("old_state")
        new_state_obj = event.data.get("new_state")

        old_state = old_state_obj.state if old_state_obj else None
        new_state = new_state_obj.state if new_state_obj else None

        _LOGGER.debug(f"State change detected: old={old_state}, new={new_state}")

        if new_state not in ("on", "off"):
            _LOGGER.debug(f"Ignoring invalid state: {new_state}")
            return

        if old_state is None:
            _LOGGER.debug("Initial state, ignoring.")
            return

        if old_state not in ("on", "off"):
            _LOGGER.debug(f"Ignoring invalid old state: {old_state}")
            return

        volume = 0.0
        flipped = False

        if old_state != new_state:
            # Actual transition
            flipped = True
            if new_state == "on":
                self._flips_on += 1
                self._total_flips_on += 1
                volume = self._volume_per_tilt_on
            elif new_state == "off":
                self._flips_off += 1
                self._total_flips_off += 1
                volume = self._volume_per_tilt_off
        elif self._enable_missed_flip_recovery:
            # Same state, but event fired: assume missed even number of flips (at least two)
            _LOGGER.debug("Same state event: assuming missed flips")
            flipped = True
            if old_state == "on":
                self._flips_off += 1  # Missed to off
                self._flips_on += 1  # Missed back to on
                self._total_flips_off += 1
                self._total_flips_on += 1
                volume = self._volume_per_tilt_off + self._volume_per_tilt_on
            elif old_state == "off":
                self._flips_on += 1  # Missed to on
                self._flips_off += 1  # Missed back to off
                self._total_flips_on += 1
                self._total_flips_off += 1
                volume = self._volume_per_tilt_on + self._volume_per_tilt_off

        if flipped:
            now = datetime.now(dt_util.get_default_time_zone())
            self._tip_history.append((now, volume))
            self._prune_history()
            self._update_rate()

        self.update_state()

    def update_state(self) -> None:
        """Calculate rainfall in mm and notify the entities."""
        daily_volume_ml = (self._volume_per_tilt_on * self._flips_on) + (
            self._volume_per_tilt_off * self._flips_off
        )
        self._state = (
            round(daily_volume_ml * self._factor_per_ml, 1)
            if daily_volume_ml >= 0
            else 0.0
        )
        total_volume_ml = (self._volume_per_tilt_on * self._total_flips_on) + (
            self._volume_per_tilt_off * self._total_flips_off
        )
        self._total_state = (
            round(total_volume_ml * self._factor_per_ml, 1)
            if total_volume_ml >= 0
            else 0.0
        )

        # Update all entities if available
        for entity in [
            self.daily_on_entity,
            self.daily_off_entity,
            self.total_on_entity,
            self.total_off_entity,
            self.daily_rain_entity,
            self.total_rain_entity,
            self.daily_tilt_entity,
            self.total_tilt_entity,
            self.rate_entity,
        ]:
            if entity and entity.hass is not None:
                entity.async_write_ha_state()

    def _prune_history(self) -> None:
        """Remove tips older than 1 hour."""
        now = datetime.now(dt_util.get_default_time_zone())
        while self._tip_history and (now - self._tip_history[0][0]) > timedelta(
            hours=1
        ):
            self._tip_history.popleft()

    def _update_rate(self) -> None:
        """Update the rainfall rate based on tips in the last hour."""
        total_volume_ml = sum(volume for _, volume in self._tip_history)
        self._rate = (
            round(total_volume_ml * self._factor_per_ml, 1)
            if total_volume_ml >= 0
            else 0.0
        )

    async def restore_tip_history(self) -> None:
        """Restore tip history from the last hour using recorder data."""
        start_time = dt_util.utcnow() - timedelta(hours=1)
        end_time = dt_util.utcnow()

        states = await self._hass.async_add_executor_job(
            lambda: history.get_significant_states(
                self._hass,
                start_time,
                end_time,
                [self._entity_id],
                significant_changes_only=True,
            )
        )
        states = states.get(self._entity_id, [])
        if not states:
            return

        states.sort(key=lambda s: s.last_changed)
        prev_state = None
        for state in states:
            if prev_state is None:
                prev_state = state
                continue
            old = prev_state.state
            new = state.state
            if old != new and old in ("on", "off") and new in ("on", "off"):
                if new == "on":
                    volume = self._volume_per_tilt_on
                else:
                    volume = self._volume_per_tilt_off
                tip_time = state.last_changed.astimezone(
                    dt_util.get_default_time_zone()
                )
                self._tip_history.append((tip_time, volume))
            prev_state = state

        self._prune_history()
        self._update_rate()

    def schedule_midnight_reset(self) -> None:
        """Schedule reset at midnight in the system's timezone."""
        now = datetime.now(dt_util.get_default_time_zone())
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
        seconds_until_midnight = (midnight - now).total_seconds()

        self._remove_midnight_reset = async_call_later(
            self._hass, seconds_until_midnight, self.reset_sensor
        )

    @callback
    def reset_sensor(self, _: datetime) -> None:
        """Reset daily counters and state at midnight."""
        self._flips_on = 0
        self._flips_off = 0
        self.update_state()
        self.schedule_midnight_reset()

    def schedule_rate_update(self) -> None:
        """Schedule periodic update for rainfall rate."""
        self._remove_rate_update = async_track_time_interval(
            self._hass, self.periodic_rate_update, timedelta(minutes=1)
        )

    @callback
    def periodic_rate_update(self, now: datetime) -> None:
        """Periodic prune and update for rainfall rate."""
        self._prune_history()
        self._update_rate()
        if self.rate_entity:
            self.rate_entity.async_write_ha_state()

    def unload(self) -> None:
        """Clean up listeners on unload."""
        if self.remove_state_listener:
            self.remove_state_listener()
            self.remove_state_listener = None
        if self._remove_midnight_reset:
            self._remove_midnight_reset()
            self._remove_midnight_reset = None
        if self._remove_rate_update:
            self._remove_rate_update()
            self._remove_rate_update = None

    @callback
    def async_unload(self) -> None:
        """Unload callback for config entry."""
        self.unload()
