"""The Dreame Mower Implementation.

This file serves as the main entry point for the integration.
It sets up the coordinator and forwards platform setup to dedicated modules.
To add new features, simply extend the PLATFORMS tuple - each platform
will automatically route to its corresponding module (e.g., switch.py, button.py).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN, DeviceType
from .coordinator import DreameMowerCoordinator

# All available platforms
ALL_PLATFORMS = (
    Platform.LAWN_MOWER,
    Platform.VACUUM,  # For hold devices (floor washers)
    Platform.SENSOR,
    Platform.CAMERA,
    Platform.BUTTON,  # For hold device advanced features
)

# Platforms per device type
PLATFORMS_BY_DEVICE_TYPE = {
    DeviceType.MOWER: (Platform.LAWN_MOWER, Platform.SENSOR, Platform.CAMERA),
    DeviceType.HOLD: (Platform.VACUUM, Platform.SENSOR, Platform.BUTTON),
    DeviceType.VACUUM: (Platform.VACUUM, Platform.SENSOR),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dreame Mower/Hold device from a config entry."""

    # Get device type from config entry
    device_type = entry.data.get("device_type", DeviceType.MOWER)

    # Select platforms based on device type
    platforms = PLATFORMS_BY_DEVICE_TYPE.get(device_type, ALL_PLATFORMS)

    # Create coordinator
    coordinator = DreameMowerCoordinator(hass, entry=entry)

    # Connect to the device
    await coordinator.async_connect_device()

    # Start coordinator updates (minimal - may not do anything initially)
    await coordinator.async_config_entry_first_refresh()

    # Trigger initial data update to reflect current device state
    await coordinator.async_request_refresh()

    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    # Set up platforms for this device/entry.
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Get device type to determine which platforms to unload
    device_type = entry.data.get("device_type", DeviceType.MOWER)
    platforms = PLATFORMS_BY_DEVICE_TYPE.get(device_type, ALL_PLATFORMS)

    # Disconnect device before unloading
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    await coordinator.async_disconnect_device()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, platforms):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)