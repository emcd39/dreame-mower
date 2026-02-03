"""Constants for the Dreame Mower integration."""

from __future__ import annotations
from typing import Final

DOMAIN = "dreame_mower"

# Configuration constants
CONF_NOTIFY: Final = "notify"
CONF_MAP_ROTATION: Final = "map_rotation"

# Device type constants
CONF_DEVICE_TYPE: Final = "device_type"

# Data storage keys
DATA_COORDINATOR = "coordinator"

# Device types
class DeviceType:
    MOWER = "mower"      # Lawn mower
    HOLD = "hold"        # Floor washer (handheld)
    VACUUM = "vacuum"    # Robot vacuum (future)

# Supported device model prefixes
MOWER_MODELS = ["dreame.mower.", "mova.mower."]
HOLD_MODELS = ["dreame.hold.", "mova.hold."]
VACUUM_MODELS = ["dreame.vacuum.", "mova.vacuum."]