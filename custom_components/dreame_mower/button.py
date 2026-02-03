"""Button platform for Dreame hold device advanced features."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity

from .const import DATA_COORDINATOR, DOMAIN, DeviceType
from .coordinator import DreameMowerCoordinator
from .entity import DreameMowerEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame hold device buttons from a config entry."""
    coordinator: DreameMowerCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    # Only create buttons for hold devices
    # NOTE: Advanced features (self-clean, deep clean, drying) disabled
    # Handheld washers use physical buttons or different control method
    # TODO: Find correct MIoT spec for dreame.hold.w2422
    if entry.data.get("device_type") == DeviceType.HOLD:
        # No buttons for now - basic vacuum controls (start/pause/stop) should work
        pass


class DreameHoldButton(DreameMowerEntity, ButtonEntity):
    """Dreame Hold device button for advanced features."""

    def __init__(self, coordinator: DreameMowerCoordinator, button_type: str, name: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator, button_type)
        self._button_type = button_type
        self._attr_name = name
        self._attr_icon = self._get_icon(button_type)

    def _get_icon(self, button_type: str) -> str:
        """Get icon for button type."""
        icons = {
            "self_clean": "mdi:spray-bottle",
            "deep_clean": "mdi:water-pump",
            "drying": "mdi:fan",
        }
        return icons.get(button_type, "mdi:circle-outline")

    async def async_press(self, **kwargs: Any) -> None:
        """Handle button press."""
        try:
            if self._button_type == "self_clean":
                await self.coordinator.device.hold_start_self_clean()
                _LOGGER.info("Self-clean started")
            elif self._button_type == "deep_clean":
                await self.coordinator.device.hold_start_deep_clean()
                _LOGGER.info("Deep clean started")
            elif self._button_type == "drying":
                await self.coordinator.device.hold_start_drying()
                _LOGGER.info("Drying started")
        except Exception as ex:
            _LOGGER.error("Error executing %s: %s", self._button_type, ex)
