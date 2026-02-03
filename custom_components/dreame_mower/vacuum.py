"""Hold device (floor washer) platform for Dreame integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
)

from .const import DATA_COORDINATOR, DOMAIN, DeviceType
from .coordinator import DreameMowerCoordinator
from .entity import DreameMowerEntity

_LOGGER = logging.getLogger(__name__)

# Supported features for floor washer
SUPPORTED_FEATURES = (
    VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.BATTERY
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Hold device from a config entry."""
    coordinator: DreameMowerCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    # Only create hold entity if device type is 'hold'
    if entry.data.get("device_type") == DeviceType.HOLD:
        async_add_entities([DreameHoldEntity(coordinator)])


class DreameHoldEntity(DreameMowerEntity, StateVacuumEntity):
    """Dreame Hold (floor washer) entity."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the hold entity."""
        super().__init__(coordinator, "hold")

        self._attr_supported_features = SUPPORTED_FEATURES
        self._attr_icon = "mdi:mop"
        self._attr_name = None  # Use device name from coordinator

        # State tracking
        self._attr_battery_level = None
        self._attr_state = None

        # Initialize state
        self._update_state()

    def _update_state(self) -> None:
        """Update entity state from coordinator data."""
        try:
            # Get device info from coordinator
            device_info = self.coordinator.device._cloud_base.get_devices()
            if device_info and "page" in device_info:
                records = device_info["page"].get("records", [])
                for record in records:
                    if record.get("did") == self.coordinator.device.device_id:
                        # Update battery
                        self._attr_battery_level = record.get("battery")
                        # Update state based on latestStatus
                        status_code = record.get("latestStatus", 7)
                        self._attr_state = self._map_status_to_state(status_code)
                        break
        except Exception as ex:
            _LOGGER.exception("Error updating state: %s", ex)

    def _map_status_to_state(self, status_code: int) -> str | None:
        """Map device status code to HA vacuum state."""
        # Status codes for hold devices:
        # 7 = standby/docked
        # 1-6 = various working states
        if status_code == 7:
            return "docked"
        elif status_code in [1, 2, 3, 4, 5, 6]:
            return "cleaning"
        else:
            return "docked"

    @property
    def available(self) -> bool:
        """Return True if the device is available."""
        return super().available and self._attr_state is not None

    @property
    def state(self) -> str | None:
        """Return the current state of the vacuum."""
        return self._attr_state

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the vacuum."""
        return self._attr_battery_level

    async def async_start(self) -> None:
        """Start cleaning."""
        try:
            # For now, just log - will implement actual control later
            _LOGGER.info("Start cleaning requested")
            self._attr_state = "cleaning"
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error starting cleaning: %s", ex)

    async def async_pause(self) -> None:
        """Pause cleaning."""
        try:
            _LOGGER.info("Pause requested")
            self._attr_state = "paused"
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error pausing: %s", ex)

    async def async_return_to_base(self) -> None:
        """Return to dock (not applicable for handheld devices)."""
        _LOGGER.info("Return to base not supported for handheld floor washers")
