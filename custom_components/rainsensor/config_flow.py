"""Config flow for Rain Sensor integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from . import DOMAIN


class RainSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rain Sensor."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate entity ID exists and is a binary_sensor
            entity_id = user_input[CONF_ENTITY_ID]
            if not await self._validate_entity_id(entity_id):
                errors["entity_id"] = "invalid_entity"
            else:
                await self.async_set_unique_id(
                    f"rainsensor_{entity_id.replace('.', '_')}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        data_schema = vol.Schema({
            vol.Required(CONF_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["binary_sensor"])
            ),
            vol.Required("volume_per_tilt_on", default=2.0): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=100.0)
            ),
            vol.Required("volume_per_tilt_off", default=2.0): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=100.0)
            ),
            vol.Required("funnel_diameter", default=100.0): vol.All(
                vol.Coerce(float), vol.Range(min=1.0, max=1000.0)
            ),
            vol.Optional(CONF_NAME, default="Rainfall"): str,
            vol.Optional("enable_missed_flip_recovery", default=False): bool,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _validate_entity_id(self, entity_id: str) -> bool:
        """Validate if the entity ID exists and is a binary sensor."""
        registry = er.async_get(self.hass)
        entry = registry.async_get(entity_id)
        return entry is not None and entry.domain == "binary_sensor"

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return RainSensorOptionsFlowHandler(config_entry)


class RainSensorOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Rain Sensor options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            entity_id = user_input[CONF_ENTITY_ID]
            if not await self._validate_entity_id(entity_id):
                errors["entity_id"] = "invalid_entity"
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        current_config = self.config_entry.data

        data_schema = vol.Schema({
            vol.Required(
                CONF_ENTITY_ID, default=current_config.get(CONF_ENTITY_ID)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["binary_sensor"])
            ),
            vol.Required(
                "volume_per_tilt_on",
                default=current_config.get("volume_per_tilt_on", 2.0),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100.0)),
            vol.Required(
                "volume_per_tilt_off",
                default=current_config.get("volume_per_tilt_off", 2.0),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100.0)),
            vol.Required(
                "funnel_diameter",
                default=current_config.get("funnel_diameter", 100.0),
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=1000.0)),
            vol.Optional(
                CONF_NAME, default=current_config.get(CONF_NAME, "Rainfall")
            ): str,
            vol.Optional(
                "enable_missed_flip_recovery",
                default=current_config.get("enable_missed_flip_recovery", False),
            ): bool,
        })

        return self.async_show_form(
            step_id="init", data_schema=data_schema, errors=errors
        )

    async def _validate_entity_id(self, entity_id: str) -> bool:
        """Validate if the entity ID exists and is a binary sensor."""
        registry = er.async_get(self.hass)
        entry = registry.async_get(entity_id)
        return entry is not None and entry.domain == "binary_sensor"
