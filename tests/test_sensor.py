"""Test the Rain Sensor sensor."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from custom_components.rainsensor import DOMAIN, RainSensorDataHandler
from custom_components.rainsensor.sensor import (
    DailyOffCountSensorEntity,
    DailyOnCountSensorEntity,
    TotalOffCountSensorEntity,
    TotalOnCountSensorEntity,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_sensor_setup(
    hass: HomeAssistant, config_entry, enable_custom_integrations
) -> None:
    """Test sensor entities setup."""
    data_handler = RainSensorDataHandler(
        hass,
        "binary_sensor.rain_tip",
        2.0,
        2.0,
        100.0,
        "Test Rain",
        config_entry.unique_id,
        False,
    )
    hass.data[DOMAIN] = {config_entry.entry_id: data_handler}

    data_handler._flips_on = 3
    data_handler._flips_off = 2
    data_handler._total_flips_on = 6
    data_handler._total_flips_off = 4
    data_handler._state = 5.0
    data_handler._total_state = 10.0
    data_handler._rate = 2.5

    mock_add_entities = MagicMock()
    await async_setup_entry(hass, config_entry, mock_add_entities)
    await hass.async_block_till_done()

    assert mock_add_entities.called
    added_entities = mock_add_entities.call_args[0][0]
    assert len(added_entities) == 9
    daily_on_entity = added_entities[0]
    daily_off_entity = added_entities[1]
    total_on_entity = added_entities[2]
    total_off_entity = added_entities[3]
    daily_rain_entity = added_entities[4]
    total_rain_entity = added_entities[5]
    daily_tilt_entity = added_entities[6]
    total_tilt_entity = added_entities[7]
    rate_entity = added_entities[8]

    # Daily on count assertions
    assert daily_on_entity.unique_id == f"{config_entry.unique_id}_daily_on_count"
    assert daily_on_entity.name == f"{data_handler.name} Daily On Count"
    assert daily_on_entity.native_unit_of_measurement == "counts"
    assert daily_on_entity.icon == "mdi:counter"
    assert daily_on_entity.state_class == SensorStateClass.TOTAL
    assert daily_on_entity.native_value == 3

    # Daily off count assertions
    assert daily_off_entity.unique_id == f"{config_entry.unique_id}_daily_off_count"
    assert daily_off_entity.name == f"{data_handler.name} Daily Off Count"
    assert daily_off_entity.native_unit_of_measurement == "counts"
    assert daily_off_entity.icon == "mdi:counter"
    assert daily_off_entity.state_class == SensorStateClass.TOTAL
    assert daily_off_entity.native_value == 2

    # Total on count assertions
    assert total_on_entity.unique_id == f"{config_entry.unique_id}_total_on_count"
    assert total_on_entity.name == f"{data_handler.name} Total On Count"
    assert total_on_entity.native_unit_of_measurement == "counts"
    assert total_on_entity.icon == "mdi:counter"
    assert total_on_entity.state_class == SensorStateClass.TOTAL_INCREASING
    assert total_on_entity.native_value == 6

    # Total off count assertions
    assert total_off_entity.unique_id == f"{config_entry.unique_id}_total_off_count"
    assert total_off_entity.name == f"{data_handler.name} Total Off Count"
    assert total_off_entity.native_unit_of_measurement == "counts"
    assert total_off_entity.icon == "mdi:counter"
    assert total_off_entity.state_class == SensorStateClass.TOTAL_INCREASING
    assert total_off_entity.native_value == 4

    # Daily rain assertions
    assert daily_rain_entity.unique_id == f"{config_entry.unique_id}_daily"
    assert daily_rain_entity.name == f"{data_handler.name} Daily"
    assert daily_rain_entity.native_unit_of_measurement == "mm"
    assert daily_rain_entity.icon == "mdi:weather-pouring"
    assert daily_rain_entity.device_class == SensorDeviceClass.PRECIPITATION
    assert daily_rain_entity.state_class == SensorStateClass.TOTAL
    assert daily_rain_entity.native_value == 5.0

    # Total rain assertions
    assert total_rain_entity.unique_id == f"{config_entry.unique_id}_total"
    assert total_rain_entity.name == f"{data_handler.name} Total"
    assert total_rain_entity.native_unit_of_measurement == "mm"
    assert total_rain_entity.icon == "mdi:weather-pouring"
    assert total_rain_entity.device_class == SensorDeviceClass.PRECIPITATION
    assert total_rain_entity.state_class == SensorStateClass.TOTAL_INCREASING
    assert total_rain_entity.native_value == 10.0

    # Daily tilt assertions
    assert daily_tilt_entity.unique_id == f"{config_entry.unique_id}_daily_tilt"
    assert daily_tilt_entity.name == f"{data_handler.name} Daily Tilt Count"
    assert daily_tilt_entity.native_unit_of_measurement == "tips"
    assert daily_tilt_entity.icon == "mdi:counter"
    assert daily_tilt_entity.state_class == SensorStateClass.TOTAL
    assert daily_tilt_entity.native_value == 5

    # Total tilt assertions
    assert total_tilt_entity.unique_id == f"{config_entry.unique_id}_total_tilt"
    assert total_tilt_entity.name == f"{data_handler.name} Total Tilt Count"
    assert total_tilt_entity.native_unit_of_measurement == "tips"
    assert total_tilt_entity.icon == "mdi:counter"
    assert total_tilt_entity.state_class == SensorStateClass.TOTAL_INCREASING
    assert total_tilt_entity.native_value == 10

    # Rate assertions
    assert rate_entity.unique_id == f"{config_entry.unique_id}_rate"
    assert rate_entity.name == f"{data_handler.name} Rainfall Rate"
    assert rate_entity.native_unit_of_measurement == "mm/h"
    assert rate_entity.icon == "mdi:weather-rainy"
    assert rate_entity.device_class == SensorDeviceClass.PRECIPITATION_INTENSITY
    assert rate_entity.state_class == SensorStateClass.MEASUREMENT
    assert rate_entity.native_value == 2.5

    # Device info shared
    for entity in added_entities:
        assert entity.device_info == DeviceInfo(
            identifiers={(DOMAIN, config_entry.unique_id)},
            name=data_handler.name,
        )


@pytest.mark.asyncio
async def test_daily_on_restore(
    hass: HomeAssistant, enable_custom_integrations, freezer
) -> None:
    """Test restoring daily on count."""
    freezer.move_to("2025-07-17 12:00:00+00:00")
    hass.config.time_zone = "UTC"

    data_handler = RainSensorDataHandler(
        hass,
        "binary_sensor.rain_tip",
        2.0,
        2.0,
        100.0,
        "Test Rain",
        "test_unique",
        False,
    )

    entity = DailyOnCountSensorEntity(data_handler)
    entity.hass = hass

    # Restore same day
    mock_state = MagicMock()
    mock_state.state = "3"
    mock_state.last_updated = datetime.now(dt_util.get_default_time_zone())
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._flips_on == 3

    # Restore older day
    mock_state.last_updated = datetime.now(dt_util.get_default_time_zone()) - timedelta(
        days=1
    )
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._flips_on == 0

    # Invalid state
    mock_state.state = "invalid"
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._flips_on == 0

    # No state
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=None,
    ):
        await entity.async_added_to_hass()
        assert data_handler._flips_on == 0


@pytest.mark.asyncio
async def test_daily_off_restore(
    hass: HomeAssistant, enable_custom_integrations, freezer
) -> None:
    """Test restoring daily off count."""
    freezer.move_to("2025-07-17 12:00:00+00:00")
    hass.config.time_zone = "UTC"

    data_handler = RainSensorDataHandler(
        hass,
        "binary_sensor.rain_tip",
        2.0,
        2.0,
        100.0,
        "Test Rain",
        "test_unique",
        False,
    )

    entity = DailyOffCountSensorEntity(data_handler)
    entity.hass = hass

    # Restore same day
    mock_state = MagicMock()
    mock_state.state = "2"
    mock_state.last_updated = datetime.now(dt_util.get_default_time_zone())
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._flips_off == 2

    # Restore older day
    mock_state.last_updated = datetime.now(dt_util.get_default_time_zone()) - timedelta(
        days=1
    )
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._flips_off == 0


@pytest.mark.asyncio
async def test_total_on_restore(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Test restoring total on count."""
    data_handler = RainSensorDataHandler(
        hass,
        "binary_sensor.rain_tip",
        2.0,
        2.0,
        100.0,
        "Test Rain",
        "test_unique",
        False,
    )

    entity = TotalOnCountSensorEntity(data_handler)
    entity.hass = hass

    mock_state = MagicMock()
    mock_state.state = "10"
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._total_flips_on == 10

    # Invalid
    mock_state.state = "invalid"
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._total_flips_on == 0

    # No state
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=None,
    ):
        await entity.async_added_to_hass()
        assert data_handler._total_flips_on == 0


@pytest.mark.asyncio
async def test_total_off_restore(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Test restoring total off count."""
    data_handler = RainSensorDataHandler(
        hass,
        "binary_sensor.rain_tip",
        2.0,
        2.0,
        100.0,
        "Test Rain",
        "test_unique",
        False,
    )

    entity = TotalOffCountSensorEntity(data_handler)
    entity.hass = hass

    mock_state = MagicMock()
    mock_state.state = "15"
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state",
        return_value=mock_state,
    ):
        await entity.async_added_to_hass()
        assert data_handler._total_flips_off == 15
