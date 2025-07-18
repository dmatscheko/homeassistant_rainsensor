"""Test the Rain Sensor config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.rainsensor import DOMAIN


@pytest.mark.asyncio
async def test_user_flow_success(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Test successful config flow from user input."""
    with patch(
        "custom_components.rainsensor.config_flow.RainSensorConfigFlow._validate_entity_id",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        user_input = {
            CONF_ENTITY_ID: "binary_sensor.rain_tip",
            "volume_per_tilt_on": 2.5,
            "volume_per_tilt_off": 2.5,
            "funnel_diameter": 100.0,
            CONF_NAME: "Test Rain",
            "enable_missed_flip_recovery": True,
        }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Test Rain"
        assert result["data"] == user_input


@pytest.mark.asyncio
async def test_user_flow_invalid_entity(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Test config flow with invalid entity ID."""
    with patch(
        "custom_components.rainsensor.config_flow.RainSensorConfigFlow._validate_entity_id",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        user_input = {
            CONF_ENTITY_ID: "binary_sensor.invalid",
            "volume_per_tilt_on": 2.0,
            "volume_per_tilt_off": 2.0,
            "funnel_diameter": 100.0,
            CONF_NAME: "Test Rain",
            "enable_missed_flip_recovery": False,
        }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"entity_id": "invalid_entity"}


@pytest.mark.asyncio
async def test_options_flow_success(
    hass: HomeAssistant, config_entry, enable_custom_integrations
) -> None:
    """Test successful options flow."""
    with patch(
        "custom_components.rainsensor.config_flow.RainSensorOptionsFlowHandler._validate_entity_id",
        return_value=True,
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

        user_input = {
            CONF_ENTITY_ID: "binary_sensor.rain_tip",
            "volume_per_tilt_on": 3.0,
            "volume_per_tilt_off": 3.0,
            "funnel_diameter": 150.0,
            CONF_NAME: "Updated Rain",
            "enable_missed_flip_recovery": True,
        }

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == user_input
        await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_options_flow_invalid_entity(
    hass: HomeAssistant, config_entry, enable_custom_integrations
) -> None:
    """Test options flow with invalid entity ID."""
    with patch(
        "custom_components.rainsensor.config_flow.RainSensorOptionsFlowHandler._validate_entity_id",
        return_value=False,
    ):
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        user_input = {
            CONF_ENTITY_ID: "binary_sensor.invalid",
            "volume_per_tilt_on": 2.0,
            "volume_per_tilt_off": 2.0,
            "funnel_diameter": 100.0,
            CONF_NAME: "Test Rain",
            "enable_missed_flip_recovery": False,
        }

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input
        )
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"entity_id": "invalid_entity"}
