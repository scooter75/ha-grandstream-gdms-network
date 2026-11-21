"""Sensor platform for Grandstream GDMS Networking."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GrandstreamDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Grandstream GDMS sensors."""
    coordinator: GrandstreamDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        GdmsNetworkSummarySensor(coordinator, "total_aps", "Total Access Points", "mdi:access-point-network"),
        GdmsNetworkSummarySensor(coordinator, "online_aps", "Online Access Points", "mdi:access-point-check"),
        GdmsNetworkSummarySensor(coordinator, "total_clients", "Connected Clients", "mdi:devices"),
    ]

    for mac in coordinator.data.get("aps", {}):
        entities.append(GdmsApClientsSensor(coordinator, mac))

    async_add_entities(entities)


class GdmsNetworkSummarySensor(
    CoordinatorEntity[GrandstreamDataCoordinator], SensorEntity
):
    """Network-wide summary metric sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: GrandstreamDataCoordinator,
        key: str,
        name: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.network_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(coordinator.network_id))},
            name=f"GDMS {coordinator.network_name}",
            manufacturer="Grandstream Networks",
            model="GDMS Networking Cloud",
        )

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get(self._key, 0))


class GdmsApClientsSensor(
    CoordinatorEntity[GrandstreamDataCoordinator], SensorEntity
):
    """Per-Access-Point connected client count and status sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: GrandstreamDataCoordinator, mac: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        ap = coordinator.data["aps"].get(mac, {})
        ap_name = ap.get("name") or mac
        self._attr_name = "Connected Clients"
        self._attr_unique_id = f"{coordinator.network_id}_{mac}_clients"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name=ap_name,
            manufacturer="Grandstream Networks",
            model=ap.get("model", "GWN Access Point"),
            sw_version=ap.get("firmwareVersion") or ap.get("version"),
            via_device=(DOMAIN, str(coordinator.network_id)),
        )

    @property
    def native_value(self) -> int:
        ap = self.coordinator.data.get("aps", {}).get(self._mac, {})
        return int(ap.get("clients", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        ap = self.coordinator.data.get("aps", {}).get(self._mac, {})
        return {
            "mac_address": self._mac,
            "ip_address": ap.get("ip"),
            "status": ap.get("status"),
            "uptime": ap.get("uptime"),
            "channel_2g": ap.get("channel2g"),
            "channel_5g": ap.get("channel5g"),
        }
