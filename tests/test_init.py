"""Test the Rain Sensor init."""

import math
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from custom_components.rainsensor import (
    DOMAIN,
    RainSensorDataHandler,
)


@pytest.mark.asyncio
async def test_setup_entry(
    hass: HomeAssistant, config_entry, enable_custom_integrations
) -> None:
    """Test successful setup of the entry."""
    result = await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert result is True
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_unload_entry(
    hass: HomeAssistant, config_entry, enable_custom_integrations
) -> None:
    """Test unloading the entry."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ):
        result = await hass.config_entries.async_unload(config_entry.entry_id)
        assert result is True
        assert config_entry.entry_id not in hass.data.get(DOMAIN, {})
    await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_handle_state_change(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Test handling state changes."""
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

    # Precompute expected factor
    area = math.pi * (50**2)
    factor = 1000 / area

    # Mock event
    event = MagicMock()
    event.data = {
        "old_state": MagicMock(state=STATE_OFF),
        "new_state": MagicMock(state=STATE_ON),
    }
    data_handler.handle_state_change(event)
    assert data_handler._flips_on == 1
    assert data_handler._total_flips_on == 1
    assert data_handler.state == round(2.0 * factor, 1)
    assert data_handler.total_state == round(2.0 * factor, 1)
    assert data_handler.daily_tilt_count == 1
    assert data_handler.total_tilt_count == 1

    event.data = {
        "old_state": MagicMock(state=STATE_ON),
        "new_state": MagicMock(state=STATE_OFF),
    }
    data_handler.handle_state_change(event)
    assert data_handler._flips_off == 1
    assert data_handler._total_flips_off == 1
    assert data_handler.state == round(4.0 * factor, 1)
    assert data_handler.total_state == round(4.0 * factor, 1)
    assert data_handler.daily_tilt_count == 2
    assert data_handler.total_tilt_count == 2

    # Test same state without recovery
    event.data = {
        "old_state": MagicMock(state=STATE_OFF),
        "new_state": MagicMock(state=STATE_OFF),
    }
    data_handler.handle_state_change(event)
    assert data_handler._flips_off == 1  # No change
    assert data_handler._total_flips_off == 1  # No change
    assert data_handler.daily_tilt_count == 2
    assert data_handler.total_tilt_count == 2

    # Test with recovery enabled
    data_handler._enable_missed_flip_recovery = True
    data_handler.handle_state_change(event)
    assert data_handler._flips_on == 2
    assert data_handler._flips_off == 2
    assert data_handler._total_flips_on == 2
    assert data_handler._total_flips_off == 2
    assert data_handler.state == round(8.0 * factor, 1)
    assert data_handler.total_state == round(8.0 * factor, 1)
    assert data_handler.daily_tilt_count == 4
    assert data_handler.total_tilt_count == 4


@pytest.mark.asyncio
async def test_midnight_reset(
    hass: HomeAssistant, monkeypatch, enable_custom_integrations, freezer
) -> None:
    """Test midnight reset scheduling and execution."""
    freezer.move_to("2025-07-16 12:00:00+00:00")  # Explicit UTC
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
    data_handler._flips_on = 5
    data_handler._flips_off = 5
    data_handler._total_flips_on = 5
    data_handler._total_flips_off = 5
    data_handler.update_state()

    with patch(
        "custom_components.rainsensor.async_call_later", return_value=MagicMock()
    ) as mock_call_later:
        data_handler.schedule_midnight_reset()
        assert mock_call_later.called

        mock_call_later.reset_mock()

        # Simulate reset
        data_handler.reset_sensor(None)  # Callback expects dummy arg
        assert data_handler._flips_on == 0
        assert data_handler._flips_off == 0
        assert data_handler.state == 0.0
        assert data_handler._total_flips_on == 5  # Unchanged
        assert data_handler._total_flips_off == 5  # Unchanged
        assert data_handler.total_state > 0
        assert data_handler.daily_tilt_count == 0
        assert data_handler.total_tilt_count == 10
        assert mock_call_later.called  # Rescheduled

    data_handler.unload()  # Cleanup
