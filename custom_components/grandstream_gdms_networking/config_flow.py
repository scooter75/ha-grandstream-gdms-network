"""Config flow for Grandstream GDMS Networking."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrandstreamApiError, GrandstreamAuthError, GrandstreamGdmsClient
from .const import (
    CONF_APP_ID,
    CONF_BASE_URL,
    CONF_NETWORK_ID,
    CONF_SCAN_INTERVAL,
    CONF_SECRET_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    REGIONAL_SERVERS,
)


class GrandstreamGdmsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Grandstream GDMS Networking."""

    VERSION = 1

    def __init__(self) -> None:
        self._base_url: str = DEFAULT_BASE_URL
        self._app_id: str = ""
        self._secret_key: str = ""
        self._networks: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Collect API credentials and server region."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._base_url = user_input[CONF_BASE_URL].rstrip("/")
            self._app_id = user_input[CONF_APP_ID].strip()
            self._secret_key = user_input[CONF_SECRET_KEY].strip()

            session = async_get_clientsession(self.hass)
            client = GrandstreamGdmsClient(
                session, self._base_url, self._app_id, self._secret_key
            )

            try:
                networks = await client.get_networks()
            except GrandstreamAuthError:
                errors["base"] = "invalid_auth"
            except GrandstreamApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                if not networks:
                    errors["base"] = "no_networks"
                else:
                    self._networks = {
                        str(net.get("id") or net.get("networkId")): net.get(
                            "name", f"Network {net.get('id')}"
                        )
                        for net in networks
                    }
                    return await self.async_step_network()

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): vol.In(
                    REGIONAL_SERVERS
                ),
                vol.Required(CONF_APP_ID): str,
                vol.Required(CONF_SECRET_KEY): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_network(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Choose the GDMS network to monitor."""
        if user_input is not None:
            network_id = user_input[CONF_NETWORK_ID]
            network_name = self._networks[network_id]

            await self.async_set_unique_id(f"{self._base_url}_{network_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"GDMS - {network_name}",
                data={
                    CONF_BASE_URL: self._base_url,
                    CONF_APP_ID: self._app_id,
                    CONF_SECRET_KEY: self._secret_key,
                    CONF_NETWORK_ID: network_id,
                    "network_name": network_name,
                },
            )

        schema = vol.Schema(
            {vol.Required(CONF_NETWORK_ID): vol.In(self._networks)}
        )
        return self.async_show_form(step_id="network", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return GrandstreamOptionsFlow(config_entry)


class GrandstreamOptionsFlow(OptionsFlow):
    """Handle options for Grandstream GDMS Networking."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=600)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
