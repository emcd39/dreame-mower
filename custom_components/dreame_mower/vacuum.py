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

        Complete status mapping from official iotKeyValue spec:
        https://cnbj2.fds.api.xiaomi.com/000000-public/file/c9d38fbfb7e45c79cfe7830e0b8ab40099759e7d_dreame.hold.w2422_iotKeyValue_translate_20.json

        Status codes 1-33:
        """
        if status_code is None:
            return None

        # Mopping/Cleaning states → "cleaning"
        if status_code in [
            1,   # 正在洗地 / Mop in progress
            16,  # 正在洗地 / Mop in progress
            17,  # 正在洗地 / Mop in progress
            18,  # 正在洗地 / Mop in progress
            19,  # 正在洗地 / Mop in progress
            20,  # 正在洗地 / Mop in progress
            21,  # 正在洗地 / Mop in progress
            22,  # 正在洗地 / Mop in progress
            8,   # 正在吸尘 / Vacuum cleaning in progress
            9,   # 正在加注清水 / Adding water
        ]:
            return "cleaning"

        # Self-cleaning states → "cleaning"
        if status_code in [
            5,   # 正在自清洁 / Self-Cleaning
            26,  # 正在热水自清洁 / Hot water self-cleaning in progress
            27,  # 正在深度热水自清洁 / Deep hot water self-cleaning in progress
            28,  # 正在自清洁 / Self-Cleaning
        ]:
            return "cleaning"

        # Drying states → "cleaning"
        if status_code in [
            6,   # 正在烘干 / Drying
            23,  # 正在烘干 / Drying
            24,  # 正在烘干 / Drying
            25,  # 正在烘干 / Drying
            32,  # 正在快速烘干 / Fast drying in progress
            33,  # 正在快速烘干 / Fast drying in progress
        ]:
            return "cleaning"

        # Paused states → "paused"
        if status_code in [
            10,  # 洗地暂停中 / Washing floor paused
            11,  # 自清洁暂停中 / Self-Cleaning Paused
            12,  # 烘干暂停中 / Drying paused
            29,  # 吸尘暂停中 / Vacuum cleaning paused
            30,  # 热水自清洁暂停中 / Hot water self-cleaning paused
            31,  # 深度热水自清洁暂停中 / Deep hot water self-cleaning paused
        ]:
            return "paused"

        # Docked/Idle states → "docked"
        if status_code in [
            2,    # 离线 / Offline
            3,    # 待机中 / Standby
            4,    # 正在充电 / Charging
            7,    # 休眠中 / Sleeping Mode
            13,   # OTA升级中 / OTA upgrade in progress
            14,   # 语音包升级中 / Voice package upgrade in progress
            15,   # 充电完成 / Charging Completed
        ]:
            return "docked"

        # Default to docked for any unknown status
        _LOGGER.warning("Unknown status code %d, defaulting to docked", status_code)
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
