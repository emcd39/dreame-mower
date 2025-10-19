"""Property 1:1 handler for complex status/temperature data.

This module handles the complex property 1:1 which contains core status, power,
thermal, and blade cycle telemetry in a 20-byte array format.
"""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class Property11Handler:
    """Handler for property 1:1 - complex status data."""

    def __init__(self) -> None:
        """Initialize the property handler."""
        self._temperature: float | None = None
        self._mode: int | None = None
        self._submode: int | None = None
        self._battery_raw: int | None = None
        self._status_flag: int | None = None
        self._phase_marker_hi: int | None = None
        self._phase_marker_lo: int | None = None
        self._aux_code: int | None = None

    def parse_value(self, value: list[int]) -> bool:
        """Parse the complex 1:1 property value.
        
        Args:
            value: List of 20 integers representing the property data
            
        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            # Validate the data format
            if not isinstance(value, list) or len(value) != 20:
                _LOGGER.warning("Property 1:1 invalid format: expected list of 20 integers, got %s", type(value).__name__)
                return False
            
            # Check sentinels (first and last byte should be 206/0xCE)
            if value[0] != 206 or value[19] != 206:
                _LOGGER.warning("Property 1:1 invalid sentinels: start=%d, end=%d (expected 206)", value[0], value[19])
                return False
            
            # Extract payload (exclude sentinels)
            payload = value[1:19]  # p0..p17
            
            # Parse according to the byte layout from README and update internal state directly
            self._mode = int(payload[6])                    # p6: 0=dock_idle, 4=mowing, 5=mission_tail
            self._battery_raw = int(payload[10])            # p10: 0-100 direct %, ≥128 => minus 128 when charging
            self._phase_marker_hi = int(payload[11])        # p11: startup/init marker
            self._phase_marker_lo = int(payload[12])        # p12: startup/init marker  
            self._submode = int(payload[13])                # p13: 33-35 startup, 64/68 spin, 133/135 mowing, etc.
            self._aux_code = int(payload[14])               # p14: 54 early → 0 thereafter
            self._status_flag = int(payload[17])            # p17: blade/motion cycle cluster
            
            # Calculate and store temperature in Celsius
            temperature_raw = int(payload[16])              # p16: temperature in 0.1°C units
            self._temperature = float(temperature_raw) / 10.0
            return True
            
        except (IndexError, TypeError, ValueError) as ex:
            _LOGGER.error("Failed to parse property 1:1: %s", ex)
            return False

    @property
    def temperature(self) -> float | None:
        """Return the temperature from last parsed data."""
        return self._temperature

    @property
    def mode(self) -> int | None:
        """Return the current mode (0=dock_idle, 4=mowing, 5=mission_tail)."""
        return self._mode

    @property
    def submode(self) -> int | None:
        """Return the current submode."""
        return self._submode

    @property
    def battery_raw(self) -> int | None:
        """Return the raw battery value."""
        return self._battery_raw

    @property
    def status_flag(self) -> int | None:
        """Return the status flag."""
        return self._status_flag

    @property
    def phase_marker_hi(self) -> int | None:
        """Return the high phase marker (startup/init marker)."""
        return self._phase_marker_hi

    @property
    def phase_marker_lo(self) -> int | None:
        """Return the low phase marker (startup/init marker)."""
        return self._phase_marker_lo

    @property
    def aux_code(self) -> int | None:
        """Return the auxiliary code."""
        return self._aux_code