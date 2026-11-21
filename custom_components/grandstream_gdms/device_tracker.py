"""Device tracker platform for Grandstream GDMS Networking clients."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GrandstreamDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grandstream GDMS client device trackers."""
    coordinator: GrandstreamDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_macs: set[str] = set()

    @callback
    def _async_discover_clients() -> None:
        new_entities: list[GdmsClientTracker] = []
        for mac in coordinator.data.get("clients", {}):
            if mac not in tracked_macs:
                tracked_macs.add(mac)
                new_entities.append(GdmsClientTracker(coordinator, mac))
        if new_entities:
            async_add_entities(new_entities)

    _async_discover_clients()
    entry.async_on_unload(coordinator.async_add_listener(_async_discover_clients))


class GdmsClientTracker(
    CoordinatorEntity[GrandstreamDataCoordinator], ScannerEntity
):
    """Represents a client device connected to a Grandstream GWN network."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GrandstreamDataCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        client = coordinator.data.get("clients", {}).get(mac, {})
        self._attr_name = client.get("name") or client.get("hostname") or mac
        self._attr_unique_id = f"{coordinator.network_id}_client_{mac}"

    @property
    def source_type(self) -> SourceType:
        return SourceType.ROUTER

    @property
    def mac_address(self) -> str:
        return self._mac

    @property
    def is_connected(self) -> bool:
        return self._mac in self.coordinator.data.get("clients", {})

    @property
    def ip_address(self) -> str | None:
        client = self.coordinator.data.get("clients", {}).get(self._mac, {})
        return client.get("ip") or client.get("ipv4")

    @property
    def hostname(self) -> str | None:
        client = self.coordinator.data.get("clients", {}).get(self._mac, {})
        return client.get("hostname") or client.get("name")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        client = self.coordinator.data.get("clients", {}).get(self._mac, {})
        return {
            "ssid": client.get("ssid"),
            "rssi": client.get("rssi"),
            "ap_mac": client.get("apMac"),
            "ap_name": client.get("apName"),
            "channel": client.get("channel"),
            "rx_rate": client.get("rxRate"),
            "tx_rate": client.get("txRate"),
        }
