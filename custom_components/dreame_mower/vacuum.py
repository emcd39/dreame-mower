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
    | VacuumEntityFeature.STOP
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
            # Get battery from device
            self._attr_battery_level = self.coordinator.device.battery_percent

            # Get status code and map to HA state
            status_code = self.coordinator.device.status_code
            self._attr_state = self._map_status_to_state(status_code)
        except Exception as ex:
            _LOGGER.exception("Error updating state: %s", ex)

    def _map_status_to_state(self, status_code: int) -> str | None:
        """Map device status code to HA vacuum state."""
        # Status codes (shared with mower):
        # 0: no_status, 1: mowing/cleaning, 2: standby, 3: paused
        # 4: error, 5: returning, 6: charging, 11: mapping, 13: charging_complete
        if status_code == 1:
            return "cleaning"
        elif status_code == 2:
            return "docked"
        elif status_code == 3:
            return "paused"
        elif status_code == 4:
            return "error"
        elif status_code == 5:
            return "returning"
        elif status_code in [6, 13]:
            return "docked"
        else:
            # Default to docked for unknown states
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
            await self.coordinator.device.hold_start_cleaning()
            self._attr_state = "cleaning"
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error starting cleaning: %s", ex)

    async def async_pause(self) -> None:
        """Pause cleaning."""
        try:
            await self.coordinator.device.hold_pause()
            self._attr_state = "paused"
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error pausing: %s", ex)

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop cleaning."""
        try:
            await self.coordinator.device.hold_stop()
            self._attr_state = "docked"
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.error("Error stopping: %s", ex)

    async def async_return_to_base(self) -> None:
        """Return to dock (not applicable for handheld devices)."""
        _LOGGER.info("Return to base not supported for handheld floor washers")
