"""The Grandstream GDMS Networking integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrandstreamGdmsClient
from .const import (
    CONF_APP_ID,
    CONF_BASE_URL,
    CONF_NETWORK_ID,
    CONF_SCAN_INTERVAL,
    CONF_SECRET_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import GrandstreamDataCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Grandstream GDMS Networking from a config entry."""
    session = async_get_clientsession(hass)
    client = GrandstreamGdmsClient(
        session=session,
        base_url=entry.data[CONF_BASE_URL],
        app_id=entry.data[CONF_APP_ID],
        secret_key=entry.data[CONF_SECRET_KEY],
    )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = GrandstreamDataCoordinator(
        hass=hass,
        client=client,
        network_id=entry.data[CONF_NETWORK_ID],
        network_name=entry.data.get("network_name", "Network"),
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
