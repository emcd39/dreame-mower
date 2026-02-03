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
from .dreame.const import HOLD_STATUS_MAPPING

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
        """Map H20 device status code to HA vacuum state.

        H20 status codes (from HOLD_STATUS_MAPPING):
        - 1: mopping → cleaning
        - 2: offline → docked
        - 3: standby → docked
        - 4: charging → docked
        - 5, 26, 28: self_cleaning → cleaning
        - 6: drying → cleaning
        - 7: sleeping → docked
        - 8: vacuuming → cleaning
        - 9: adding_water → cleaning
        - 10, 11, 12: paused → paused
        - 13, 14: updating → docked
        - 15: charged → docked
        - 27: deep_cleaning → cleaning
        - 32, 33: fast_drying → cleaning
        """
        if status_code is None:
            return None

        # Get the H20 status from HOLD_STATUS_MAPPING
        h20_status = HOLD_STATUS_MAPPING.get(status_code, "standby")

        # Map H20 status to HA vacuum states
        if h20_status in ["mopping", "vacuuming", "adding_water",
                         "self_cleaning", "hot_water_cleaning", "deep_cleaning",
                         "drying", "fast_drying"]:
            return "cleaning"
        elif h20_status in ["offline", "standby", "charging", "charged",
                           "sleeping", "updating"]:
            return "docked"
        elif h20_status == "paused":
            return "paused"
        elif h20_status == "error":
            return "error"
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
