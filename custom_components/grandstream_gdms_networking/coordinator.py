"""DataUpdateCoordinator for Grandstream GDMS Networking."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GrandstreamAuthError, GrandstreamGdmsClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GrandstreamDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch network devices and clients from GDMS."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: GrandstreamGdmsClient,
        network_id: int | str,
        network_name: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{network_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.network_id = network_id
        self.network_name = network_name

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest APs and clients from GDMS API."""
        try:
            aps = await self.client.get_access_points(self.network_id)
            clients = await self.client.get_connected_clients(self.network_id)
        except GrandstreamAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with GDMS API: {err}") from err

        aps_by_mac = {
            ap.get("mac", "").upper(): ap for ap in aps if ap.get("mac")
        }
        clients_by_mac = {
            c.get("mac", "").upper(): c for c in clients if c.get("mac")
        }

        return {
            "aps": aps_by_mac,
            "clients": clients_by_mac,
            "total_aps": len(aps_by_mac),
            "online_aps": sum(
                1 for ap in aps_by_mac.values() if ap.get("status") in (1, "online", "Online")
            ),
            "total_clients": len(clients_by_mac),
        }
