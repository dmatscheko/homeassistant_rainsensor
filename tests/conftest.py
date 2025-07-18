"""Shared fixtures for Rain Sensor tests."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.rainsensor import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_recorder_mock(recorder_mock):
    """Auto-enable recorder mock for all tests."""
    return recorder_mock


@pytest.fixture(autouse=True)
def mock_history_get_significant_states():
    """Mock history get significant states."""
    with patch(
        "homeassistant.components.recorder.history.get_significant_states",
        return_value={},
    ):
        yield


@pytest.fixture
async def config_entry(hass: HomeAssistant, enable_custom_integrations):
    """Fixture for a mock config entry."""
    entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Test Rain",
        data={
            CONF_ENTITY_ID: "binary_sensor.rain_tip",
            "volume_per_tilt_on": 2.0,
            "volume_per_tilt_off": 2.0,
            "funnel_diameter": 100.0,
            CONF_NAME: "Test Rain",
            "enable_missed_flip_recovery": False,
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_entry",
        unique_id="test_entry",
        options={},
        discovery_keys={},
    )
    entry.add_to_hass(hass)
    return entry
