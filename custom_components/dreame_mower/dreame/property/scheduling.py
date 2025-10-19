"""Scheduling property handling for Dreame Mower Implementation.

This module provides parsing and handling for Service 2 scheduling properties:
- 2:50 - Mission task descriptor (TASK object with mission details)
- 2:51 - Multi-format property with 7 known variants:
  * (a) DND schedule: {'start': X, 'end': Y, 'value': 0|1}
  * (b) Time synchronization: {'time': 'epoch', 'tz': 'timezone'}
  * (c) Charging schedule: {'value': [auto%, resume%, sep, enabled, start, end]}
  * (d) Third variant (unknown): {'value': [val1, val2, val3]}
  * (e) Fourth variant (unknown): {'value': integer}
  * (f) Fifth variant (unknown): {'value': [val1, val2, val3, val4]}
  * (g) Sixth variant (unknown): {'type': integer} - possibly obstacle avoidance or general settings
- 2:52 - Mission completion summary (currently empty, future use)

These properties manage mission lifecycle, user scheduling preferences, and completion tracking.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, Any
from enum import Enum

_LOGGER = logging.getLogger(__name__)

# Property 2:51 variant notification names (sub-types of scheduling_dnd)
# These are not actual MQTT properties but internal notification types
SCHEDULING_TIME_SYNC_PROPERTY_NAME = "scheduling_time_sync"
SCHEDULING_CHARGING_PROPERTY_NAME = "scheduling_charging"
SCHEDULING_THIRD_VARIANT_PROPERTY_NAME = "scheduling_third_variant"
SCHEDULING_FOURTH_VARIANT_PROPERTY_NAME = "scheduling_fourth_variant"
SCHEDULING_FIFTH_VARIANT_PROPERTY_NAME = "scheduling_fifth_variant"
SCHEDULING_SIXTH_VARIANT_PROPERTY_NAME = "scheduling_sixth_variant"

# Task data field constants
TASK_TYPE_FIELD = "type"
TASK_AREA_ID_FIELD = "area_id"
TASK_EXECUTION_FIELD = "execution_active"
TASK_COVERAGE_FIELD = "coverage_target"
TASK_REGION_ID_FIELD = "region_id"
TASK_STATUS_FIELD = "task_active"
TASK_TIME_FIELD = "elapsed_time"

# DND data field constants
DND_START_FIELD = "start_minute"
DND_END_FIELD = "end_minute"
DND_ENABLED_FIELD = "enabled"

# Time sync data field constants
TIME_SYNC_TIMESTAMP_FIELD = "timestamp"
TIME_SYNC_TIMEZONE_FIELD = "timezone"

# Charging schedule data field constants
CHARGING_AUTO_RECHARGE_FIELD = "auto_recharge_percent"
CHARGING_RESUME_FIELD = "resume_percent"
CHARGING_ENABLED_FIELD = "enabled"
CHARGING_START_FIELD = "start_minute"
CHARGING_END_FIELD = "end_minute"

# Third variant data field constants (placeholder)
THIRD_VARIANT_VALUE1_FIELD = "value1"
THIRD_VARIANT_VALUE2_FIELD = "value2"
THIRD_VARIANT_VALUE3_FIELD = "value3"

# Fourth variant data field constants (single integer value)
FOURTH_VARIANT_VALUE_FIELD = "value"

# Fifth variant data field constants (4-element array)
FIFTH_VARIANT_VALUE1_FIELD = "value1"
FIFTH_VARIANT_VALUE2_FIELD = "value2"
FIFTH_VARIANT_VALUE3_FIELD = "value3"
FIFTH_VARIANT_VALUE4_FIELD = "value4"

# Sixth variant data field constants (single 'type' integer value)
SIXTH_VARIANT_TYPE_FIELD = "type"


class TaskType(Enum):
    """Task type enumeration."""
    TASK = "TASK"
    UNKNOWN = "UNKNOWN"


class Property51Type(Enum):
    """Property 2:51 payload type enumeration."""
    DND_SCHEDULE = "dnd_schedule"
    TIME_SYNC = "time_sync"
    CHARGING_SCHEDULE = "charging_schedule"
    THIRD_VARIANT = "third_variant"
    FOURTH_VARIANT = "fourth_variant"
    FIFTH_VARIANT = "fifth_variant"
    SIXTH_VARIANT = "sixth_variant"
    UNKNOWN = "unknown"


def _parse_python_literal_to_json(value_str: str) -> Dict[str, Any]:
    """Parse Python string literal to JSON dictionary."""
    try:
        # Convert Python literals to JSON format
        cleaned = (value_str
                  .replace("'", '"')          # Single to double quotes
                  .replace('True', 'true')    # Python bool to JSON bool  
                  .replace('False', 'false'))  # Python bool to JSON bool
        
        return json.loads(cleaned)
    except json.JSONDecodeError as ex:
        raise ValueError(f"Failed to parse Python literal: {value_str}") from ex


class TaskHandler:
    """Handler for mission task descriptor property (2:50)."""
    
    def __init__(self) -> None:
        """Initialize task handler."""
        self._task_type: TaskType | None = None
        self._area_id: list[int] | None = None
        self._execution_active: bool | None = None
        self._coverage_target: int | None = None
        self._region_id: list[int] | None = None
        self._task_active: bool | None = None
        self._elapsed_time: int | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse task descriptor value."""
        try:
            # Handle string literal format (from MQTT)
            if isinstance(value, str):
                parsed_data = _parse_python_literal_to_json(value)
            elif isinstance(value, dict):
                parsed_data = value
            else:
                _LOGGER.warning("Invalid task descriptor value type: %s", type(value))
                return False
            
            # Extract task type - required field
            task_type_str = parsed_data["t"]
            self._task_type = TaskType.TASK if task_type_str == "TASK" else TaskType.UNKNOWN
            
            # Extract task data from 'd' field - required
            task_data = parsed_data["d"]
            if not isinstance(task_data, dict):
                raise ValueError(f"Invalid task data format: {task_data}")
            
            # Extract required task fields - let KeyError bubble up for missing required fields
            self._execution_active = task_data["exe"]
            self._coverage_target = task_data["o"]
            self._task_active = task_data["status"]
            
            # Extract optional task fields (may not be present for paused/docked states)
            self._area_id = task_data.get("area_id")
            self._region_id = task_data.get("region_id")
            self._elapsed_time = task_data.get("time")
            
            _LOGGER.debug(
                "Task descriptor parsed: type=%s, regions=%s, elapsed=%s, active=%s, execution_active=%s",
                self._task_type, self._region_id, self._elapsed_time, self._task_active, self._execution_active
            )
            return True
            
        except (KeyError, ValueError) as ex:
            _LOGGER.error("Failed to parse task descriptor - missing or invalid field: %s", ex)
            return False
        except Exception as ex:
            _LOGGER.error("Failed to parse task descriptor: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get task notification data for Home Assistant."""
        return {
            TASK_TYPE_FIELD: self._task_type.value if self._task_type else None,
            TASK_AREA_ID_FIELD: self._area_id,
            TASK_EXECUTION_FIELD: self._execution_active,
            TASK_COVERAGE_FIELD: self._coverage_target,
            TASK_REGION_ID_FIELD: self._region_id,
            TASK_STATUS_FIELD: self._task_active,
            TASK_TIME_FIELD: self._elapsed_time,
        }
    
    # Properties for direct access
    @property
    def task_type(self) -> TaskType | None:
        """Return task type."""
        return self._task_type
    
    @property
    def area_id(self) -> list[int] | None:
        """Return selected area IDs."""
        return self._area_id
    
    @property
    def execution_active(self) -> bool | None:
        """Return True if task execution is active."""
        return self._execution_active
    
    @property
    def coverage_target(self) -> int | None:
        """Return coverage target percentage or mode sentinel."""
        return self._coverage_target
    
    @property
    def region_id(self) -> list[int] | None:
        """Return working region IDs."""
        return self._region_id
    
    @property
    def task_active(self) -> bool | None:
        """Return True if task is active/accepted."""
        return self._task_active
    
    @property
    def elapsed_time(self) -> int | None:
        """Return elapsed time in seconds at snapshot."""
        return self._elapsed_time


class DndTimeHandler:
    """Handler for DND schedule and time sync property (2:51) with dual schema support."""
    
    def __init__(self) -> None:
        """Initialize DND/time handler."""
        # DND schedule fields
        self._dnd_start_minute: int | None = None
        self._dnd_end_minute: int | None = None
        self._dnd_enabled: bool | None = None
        
        # Time sync fields
        self._sync_timestamp: str | None = None
        self._sync_timezone: str | None = None
        
        # Current payload type
        self._payload_type: Property51Type = Property51Type.UNKNOWN
        
        # Additional handlers for new variants
        self._charging_handler = ChargingHandler()
        self._third_variant_handler = ThirdVariantHandler()
        self._fourth_variant_handler = FourthVariantHandler()
        self._fifth_variant_handler = FifthVariantHandler()
        self._sixth_variant_handler = SixthVariantHandler()
    
    def parse_value(self, value: Any) -> bool:
        """Parse DND schedule, time sync, charging schedule, or third variant value with automatic format detection."""
        try:
            # Handle string literal format (from MQTT)
            if isinstance(value, str):
                parsed_data = _parse_python_literal_to_json(value)
            elif isinstance(value, dict):
                parsed_data = value
            else:
                _LOGGER.warning("Invalid DND/time/charging value type: %s", type(value))
                return False
            
            # Auto-detect payload type based on fields
            if all(key in parsed_data for key in ['start', 'end', 'value']) and isinstance(parsed_data['value'], int):
                # DND schedule format: {'start': X, 'end': Y, 'value': Z}
                self._payload_type = Property51Type.DND_SCHEDULE
                return self._parse_dnd_schedule(parsed_data)
            elif all(key in parsed_data for key in ['time', 'tz']):
                # Time sync format: {'time': 'timestamp', 'tz': 'timezone'}
                self._payload_type = Property51Type.TIME_SYNC
                return self._parse_time_sync(parsed_data)
            elif 'value' in parsed_data and isinstance(parsed_data['value'], list):
                # Array format - could be charging schedule, third variant, or fifth variant
                value_array = parsed_data['value']
                if len(value_array) == 6:
                    # Charging schedule format: {'value': [auto_recharge%, resume%, separator, enabled, start_min, end_min]}
                    self._payload_type = Property51Type.CHARGING_SCHEDULE
                    return self._charging_handler.parse_value(parsed_data)
                elif len(value_array) == 4:
                    # Fifth variant format: {'value': [val1, val2, val3, val4]}
                    self._payload_type = Property51Type.FIFTH_VARIANT
                    return self._fifth_variant_handler.parse_value(parsed_data)
                elif len(value_array) == 3:
                    # Third variant format: {'value': [val1, val2, val3]}
                    self._payload_type = Property51Type.THIRD_VARIANT
                    return self._third_variant_handler.parse_value(parsed_data)
                else:
                    _LOGGER.warning("Unknown array format for property 2:51: %s", value)
                    self._payload_type = Property51Type.UNKNOWN
                    return False
            elif 'value' in parsed_data and isinstance(parsed_data['value'], int):
                # Single integer value format - fourth variant
                # Note: This check must come after DND schedule check to avoid conflicts
                self._payload_type = Property51Type.FOURTH_VARIANT
                return self._fourth_variant_handler.parse_value(parsed_data)
            elif 'type' in parsed_data and isinstance(parsed_data['type'], int):
                # Sixth variant format: {'type': integer}
                # Seen when changing general settings (e.g., obstacle avoidance)
                self._payload_type = Property51Type.SIXTH_VARIANT
                return self._sixth_variant_handler.parse_value(parsed_data)
            else:
                _LOGGER.warning("Unknown property 2:51 format: %s", value)
                self._payload_type = Property51Type.UNKNOWN
                return False
                
        except Exception as ex:
            _LOGGER.error("Failed to parse DND/time/charging property: %s", ex)
            self._payload_type = Property51Type.UNKNOWN
            return False
    
    def _parse_dnd_schedule(self, data: Dict[str, Any]) -> bool:
        """Parse DND schedule data."""
        try:
            self._dnd_start_minute = int(data['start'])
            self._dnd_end_minute = int(data['end'])
            self._dnd_enabled = bool(data['value'])
            
            # Clear time sync fields
            self._sync_timestamp = None
            self._sync_timezone = None
            
            _LOGGER.debug(
                "DND schedule parsed: start=%d, end=%d, enabled=%s",
                self._dnd_start_minute, self._dnd_end_minute, self._dnd_enabled
            )
            return True
            
        except (ValueError, KeyError) as ex:
            _LOGGER.error("Failed to parse DND schedule: %s", ex)
            return False
    
    def _parse_time_sync(self, data: Dict[str, Any]) -> bool:
        """Parse time sync data."""
        try:
            self._sync_timestamp = str(data['time'])
            self._sync_timezone = str(data['tz'])
            
            # Clear DND fields
            self._dnd_start_minute = None
            self._dnd_end_minute = None
            self._dnd_enabled = None
            return True
            
        except (ValueError, KeyError) as ex:
            _LOGGER.error("Failed to parse time sync: %s", ex)
            return False
    
    def get_dnd_notification_data(self) -> Dict[str, Any] | None:
        """Get DND notification data for Home Assistant."""
        if self._payload_type != Property51Type.DND_SCHEDULE:
            return None
            
        return {
            DND_START_FIELD: self._dnd_start_minute,
            DND_END_FIELD: self._dnd_end_minute,
            DND_ENABLED_FIELD: self._dnd_enabled,
        }
    
    def get_time_sync_notification_data(self) -> Dict[str, Any] | None:
        """Get time sync notification data for Home Assistant.
        
        Returns:
            Dictionary with time sync data, or None if not time sync payload
        """
        if self._payload_type != Property51Type.TIME_SYNC:
            return None
            
        return {
            TIME_SYNC_TIMESTAMP_FIELD: self._sync_timestamp,
            TIME_SYNC_TIMEZONE_FIELD: self._sync_timezone,
        }
    
    def get_charging_notification_data(self) -> Dict[str, Any] | None:
        """Get charging schedule notification data for Home Assistant.
        
        Returns:
            Dictionary with charging data, or None if not charging payload
        """
        if self._payload_type != Property51Type.CHARGING_SCHEDULE:
            return None
            
        return self._charging_handler.get_notification_data()
    
    def get_third_variant_notification_data(self) -> Dict[str, Any] | None:
        """Get third variant notification data for Home Assistant.
        
        Returns:
            Dictionary with third variant data, or None if not third variant payload
        """
        if self._payload_type != Property51Type.THIRD_VARIANT:
            return None
            
        return self._third_variant_handler.get_notification_data()
    
    def get_fourth_variant_notification_data(self) -> Dict[str, Any] | None:
        """Get fourth variant notification data for Home Assistant.
        
        Returns:
            Dictionary with fourth variant data, or None if not fourth variant payload
        """
        if self._payload_type != Property51Type.FOURTH_VARIANT:
            return None
            
        return self._fourth_variant_handler.get_notification_data()
    
    def get_fifth_variant_notification_data(self) -> Dict[str, Any] | None:
        """Get fifth variant notification data for Home Assistant.
        
        Returns:
            Dictionary with fifth variant data, or None if not fifth variant payload
        """
        if self._payload_type != Property51Type.FIFTH_VARIANT:
            return None
            
        return self._fifth_variant_handler.get_notification_data()
    
    def get_sixth_variant_notification_data(self) -> Dict[str, Any] | None:
        """Get sixth variant notification data for Home Assistant.
        
        Returns:
            Dictionary with sixth variant data, or None if not sixth variant payload
        """
        if self._payload_type != Property51Type.SIXTH_VARIANT:
            return None
            
        return self._sixth_variant_handler.get_notification_data()
    
    # Properties for direct access
    @property
    def payload_type(self) -> Property51Type:
        """Return current payload type."""
        return self._payload_type
    
    @property
    def dnd_start_minute(self) -> int | None:
        """Return DND start minute (minutes from midnight)."""
        return self._dnd_start_minute
    
    @property
    def dnd_end_minute(self) -> int | None:
        """Return DND end minute (minutes from midnight)."""
        return self._dnd_end_minute
    
    @property
    def dnd_enabled(self) -> bool | None:
        """Return DND enabled status."""
        return self._dnd_enabled
    
    @property
    def sync_timestamp(self) -> str | None:
        """Return time sync timestamp."""
        return self._sync_timestamp
    
    @property
    def sync_timezone(self) -> str | None:
        """Return time sync timezone."""
        return self._sync_timezone
    
    @property
    def charging_handler(self) -> ChargingHandler:
        """Return charging handler for direct access."""
        return self._charging_handler
    
    @property
    def third_variant_handler(self) -> ThirdVariantHandler:
        """Return third variant handler for direct access."""
        return self._third_variant_handler
    
    @property
    def fourth_variant_handler(self) -> FourthVariantHandler:
        """Return fourth variant handler for direct access."""
        return self._fourth_variant_handler
    
    @property
    def fifth_variant_handler(self) -> FifthVariantHandler:
        """Return fifth variant handler for direct access."""
        return self._fifth_variant_handler
    
    @property
    def sixth_variant_handler(self) -> SixthVariantHandler:
        """Return sixth variant handler for direct access."""
        return self._sixth_variant_handler


class ChargingHandler:
    """Handler for charging schedule property (2:51 charging variant)."""
    
    def __init__(self) -> None:
        """Initialize charging handler."""
        self._auto_recharge_percent: int | None = None
        self._resume_percent: int | None = None
        self._enabled: bool | None = None
        self._start_minute: int | None = None
        self._end_minute: int | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse charging schedule value."""
        try:
            # Handle dict format with 'value' array
            if isinstance(value, dict) and 'value' in value:
                value_array = value['value']
                if not isinstance(value_array, list) or len(value_array) != 6:
                    _LOGGER.warning("Invalid charging schedule array format: %s", value)
                    return False
                
                # Parse charging schedule format: [auto_recharge%, resume%, separator, enabled, start_min, end_min]
                self._auto_recharge_percent = int(value_array[0])
                self._resume_percent = int(value_array[1])
                # value_array[2] is separator, ignore for now
                self._enabled = bool(value_array[3])
                self._start_minute = int(value_array[4])
                self._end_minute = int(value_array[5])
                
                _LOGGER.debug(
                    "Charging schedule parsed: auto_recharge=%d%%, resume=%d%%, enabled=%s, start=%d, end=%d",
                    self._auto_recharge_percent, self._resume_percent, self._enabled,
                    self._start_minute, self._end_minute
                )
                return True
            else:
                _LOGGER.warning("Invalid charging schedule value format: %s", value)
                return False
                
        except (ValueError, KeyError, IndexError) as ex:
            _LOGGER.error("Failed to parse charging schedule: %s", ex)
            return False
        except Exception as ex:
            _LOGGER.error("Failed to parse charging schedule: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get charging notification data for Home Assistant."""
        return {
            CHARGING_AUTO_RECHARGE_FIELD: self._auto_recharge_percent,
            CHARGING_RESUME_FIELD: self._resume_percent,
            CHARGING_ENABLED_FIELD: self._enabled,
            CHARGING_START_FIELD: self._start_minute,
            CHARGING_END_FIELD: self._end_minute,
        }
    
    # Properties for direct access
    @property
    def auto_recharge_percent(self) -> int | None:
        """Return auto-recharge battery percentage."""
        return self._auto_recharge_percent
    
    @property
    def resume_percent(self) -> int | None:
        """Return resume task battery percentage."""
        return self._resume_percent
    
    @property
    def enabled(self) -> bool | None:
        """Return custom charging period enabled status."""
        return self._enabled
    
    @property
    def start_minute(self) -> int | None:
        """Return charging period start minute (minutes from midnight)."""
        return self._start_minute
    
    @property
    def end_minute(self) -> int | None:
        """Return charging period end minute (minutes from midnight)."""
        return self._end_minute


class ThirdVariantHandler:
    """Handler for third variant property (2:51 third variant) - placeholder implementation."""
    
    def __init__(self) -> None:
        """Initialize third variant handler."""
        self._value1: int | None = None
        self._value2: int | None = None
        self._value3: int | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse third variant value - placeholder implementation."""
        try:
            # Handle dict format with 'value' array
            if isinstance(value, dict) and 'value' in value:
                value_array = value['value']
                if not isinstance(value_array, list) or len(value_array) != 3:
                    _LOGGER.warning("Invalid third variant array format: %s", value)
                    return False
                
                # TODO: Determine actual meaning of these values when we understand the format
                # Example values seen: [3198, 9591, 0]
                # Hypothesis: Could be related to DND settings in an alternate format,
                # timing parameters, or device state. Values don't match typical 
                # minute-of-day format (0-1439), so may represent seconds, durations,
                # or other configuration parameters.
                self._value1 = int(value_array[0])
                self._value2 = int(value_array[1])
                self._value3 = int(value_array[2])
                
                _LOGGER.info(
                    "Property 2:51 third variant received (unknown interpretation): [%d, %d, %d]. "
                    "This format is not yet fully understood. If you know what device state "
                    "corresponds to these values, please report to the project maintainer.",
                    self._value1, self._value2, self._value3
                )
                return True
            else:
                _LOGGER.warning("Invalid third variant value format: %s", value)
                return False
                
        except (ValueError, KeyError, IndexError) as ex:
            _LOGGER.error("Failed to parse third variant: %s", ex)
            return False
        except Exception as ex:
            _LOGGER.error("Failed to parse third variant: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get third variant notification data for Home Assistant."""
        return {
            THIRD_VARIANT_VALUE1_FIELD: self._value1,
            THIRD_VARIANT_VALUE2_FIELD: self._value2,
            THIRD_VARIANT_VALUE3_FIELD: self._value3,
        }
    
    # Properties for direct access
    @property
    def value1(self) -> int | None:
        """Return first value (placeholder)."""
        return self._value1
    
    @property
    def value2(self) -> int | None:
        """Return second value (placeholder)."""
        return self._value2
    
    @property
    def value3(self) -> int | None:
        """Return third value (placeholder)."""
        return self._value3


class FourthVariantHandler:
    """Handler for fourth variant property (2:51 fourth variant) - single integer value."""
    
    def __init__(self) -> None:
        """Initialize fourth variant handler."""
        self._value: int | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse fourth variant value - single integer format."""
        try:
            # Handle dict format with single 'value' integer
            if isinstance(value, dict) and 'value' in value:
                if isinstance(value['value'], int):
                    self._value = int(value['value'])
                    
                    _LOGGER.info(
                        "Property 2:51 fourth variant received (unknown interpretation): %d. "
                        "This format is not yet fully understood. If you know what device state "
                        "corresponds to this value, please report to the project maintainer.",
                        self._value
                    )
                    return True
                else:
                    _LOGGER.warning("Invalid fourth variant value type (expected int): %s", type(value['value']))
                    return False
            else:
                _LOGGER.warning("Invalid fourth variant value format: %s", value)
                return False
                
        except (ValueError, KeyError) as ex:
            _LOGGER.error("Failed to parse fourth variant: %s", ex)
            return False
        except Exception as ex:
            _LOGGER.error("Failed to parse fourth variant: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get fourth variant notification data for Home Assistant."""
        return {
            FOURTH_VARIANT_VALUE_FIELD: self._value,
        }
    
    # Properties for direct access
    @property
    def value(self) -> int | None:
        """Return the single integer value."""
        return self._value


class FifthVariantHandler:
    """Handler for fifth variant property (2:51 fifth variant) - 4-element array."""
    
    def __init__(self) -> None:
        """Initialize fifth variant handler."""
        self._value1: int | None = None
        self._value2: int | None = None
        self._value3: int | None = None
        self._value4: int | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse fifth variant value - 4-element array format."""
        try:
            # Handle dict format with 'value' array
            if isinstance(value, dict) and 'value' in value:
                value_array = value['value']
                if not isinstance(value_array, list) or len(value_array) != 4:
                    _LOGGER.warning("Invalid fifth variant array format: %s", value)
                    return False
                
                # Parse 4-element array format
                # Example values seen: [1, 1, 0, 0]
                # Interpretation is unknown - could be flags, mode indicators, or configuration values
                self._value1 = int(value_array[0])
                self._value2 = int(value_array[1])
                self._value3 = int(value_array[2])
                self._value4 = int(value_array[3])
                
                _LOGGER.info(
                    "Property 2:51 fifth variant received (unknown interpretation): [%d, %d, %d, %d]. "
                    "This format is not yet fully understood. If you know what device state "
                    "corresponds to these values, please report to the project maintainer.",
                    self._value1, self._value2, self._value3, self._value4
                )
                return True
            else:
                _LOGGER.warning("Invalid fifth variant value format: %s", value)
                return False
                
        except (ValueError, KeyError, IndexError) as ex:
            _LOGGER.error("Failed to parse fifth variant: %s", ex)
            return False
        except Exception as ex:
            _LOGGER.error("Failed to parse fifth variant: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get fifth variant notification data for Home Assistant."""
        return {
            FIFTH_VARIANT_VALUE1_FIELD: self._value1,
            FIFTH_VARIANT_VALUE2_FIELD: self._value2,
            FIFTH_VARIANT_VALUE3_FIELD: self._value3,
            FIFTH_VARIANT_VALUE4_FIELD: self._value4,
        }
    
    # Properties for direct access
    @property
    def value1(self) -> int | None:
        """Return first value (placeholder)."""
        return self._value1
    
    @property
    def value2(self) -> int | None:
        """Return second value (placeholder)."""
        return self._value2
    
    @property
    def value3(self) -> int | None:
        """Return third value (placeholder)."""
        return self._value3
    
    @property
    def value4(self) -> int | None:
        """Return fourth value (placeholder)."""
        return self._value4


class SixthVariantHandler:
    """Handler for sixth variant property (2:51 sixth variant) - {'type': integer} format.
    
    This variant was discovered when user changed general settings (obstacle avoidance).
    The exact interpretation is not yet fully understood but appears to be related to
    device configuration options.
    """
    
    def __init__(self) -> None:
        """Initialize sixth variant handler."""
        self._type_value: int | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse sixth variant value - {'type': integer} format."""
        try:
            # Handle dict format with 'type' integer
            if isinstance(value, dict) and 'type' in value:
                if isinstance(value['type'], int):
                    self._type_value = int(value['type'])
                    
                    _LOGGER.info(
                        "Property 2:51 sixth variant received (type=%d). "
                        "This format appears when changing general settings (e.g., obstacle avoidance). "
                        "If you know what device state corresponds to this value, "
                        "please report to the project maintainer.",
                        self._type_value
                    )
                    return True
                else:
                    _LOGGER.warning("Invalid sixth variant type value type (expected int): %s", type(value['type']))
                    return False
            else:
                _LOGGER.warning("Invalid sixth variant value format: %s", value)
                return False
                
        except (ValueError, KeyError) as ex:
            _LOGGER.error("Failed to parse sixth variant: %s", ex)
            return False
        except Exception as ex:
            _LOGGER.error("Failed to parse sixth variant: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get sixth variant notification data for Home Assistant."""
        return {
            SIXTH_VARIANT_TYPE_FIELD: self._type_value,
        }
    
    # Properties for direct access
    @property
    def type_value(self) -> int | None:
        """Return the type integer value."""
        return self._type_value


class SummaryHandler:
    """Handler for mission completion summary property (2:52)."""
    
    def __init__(self) -> None:
        """Initialize summary handler."""
        self._summary_data: Dict[str, Any] = {}
    
    def parse_value(self, value: Any) -> bool:
        """Parse mission summary value."""
        try:
            if isinstance(value, dict):
                self._summary_data = value.copy()
            elif value == {}:
                # Empty dict is valid (current behavior)
                self._summary_data = {}
            else:
                _LOGGER.warning("Invalid summary value type: %s", type(value))
                return False
            
            _LOGGER.debug("Mission summary parsed: %s", self._summary_data)
            return True
            
        except Exception as ex:
            _LOGGER.error("Failed to parse mission summary: %s", ex)
            return False
    
    def get_notification_data(self) -> Dict[str, Any]:
        """Get summary notification data for Home Assistant."""
        # Return raw data for now, add specific field extraction when populated
        return self._summary_data.copy()
    
    @property
    def summary_data(self) -> Dict[str, Any]:
        """Return raw summary data."""
        return self._summary_data.copy()
    
    @property
    def is_empty(self) -> bool:
        """Return True if summary is empty."""
        return len(self._summary_data) == 0


class SchedulingPropertyHandler:
    """Combined handler for all scheduling properties (2:50, 2:51, 2:52) with state management."""
    
    def __init__(self) -> None:
        """Initialize scheduling property handler."""
        self._task_handler = TaskHandler()
        self._dnd_time_handler = DndTimeHandler()
        self._summary_handler = SummaryHandler()
        
        # State storage - single source of truth for scheduling-related device state
        self._dnd_enabled: bool | None = None
        self._dnd_start_time: int | None = None  # Minutes from midnight
        self._dnd_end_time: int | None = None    # Minutes from midnight
        self._timezone: str | None = None
        self._device_time: str | None = None
    
    def handle_property_update(self, siid: int, piid: int, value: Any, notify_callback) -> bool:
        """Handle any scheduling property update with unified logic.
        
        This is the main entry point for all scheduling properties (2:50, 2:51, 2:52).
        
        Args:
            siid: Service instance ID
            piid: Property instance ID  
            value: Property value from MQTT
            notify_callback: Callback function for property change notifications
            
        Returns:
            True if property was handled successfully, False otherwise
        """
        from ..const import SCHEDULING_TASK_PROPERTY, SCHEDULING_DND_PROPERTY, SCHEDULING_SUMMARY_PROPERTY
        
        try:
            # Handle task descriptor (2:50)
            if SCHEDULING_TASK_PROPERTY.matches(siid, piid):
                return self._handle_task_property(value, notify_callback)
            
            # Handle DND/time sync (2:51)  
            elif SCHEDULING_DND_PROPERTY.matches(siid, piid):
                return self._handle_dnd_time_property(value, notify_callback)
            
            # Handle summary (2:52)
            elif SCHEDULING_SUMMARY_PROPERTY.matches(siid, piid):
                return self._handle_summary_property(value, notify_callback)
            
            else:
                # Not a scheduling property
                return False
                
        except Exception as ex:
            _LOGGER.error("Failed to handle scheduling property %d:%d: %s", siid, piid, ex)
            return False
    
    def _handle_task_property(self, value: Any, notify_callback) -> bool:
        """Handle mission task descriptor (2:50)."""
        from ..const import SCHEDULING_TASK_PROPERTY
        
        if self._task_handler.parse_value(value):
            task_data = self._task_handler.get_notification_data()
            notify_callback(SCHEDULING_TASK_PROPERTY.name, task_data)
            _LOGGER.info("Mission task started: %s", task_data)
            return True
        else:
            _LOGGER.warning("Failed to parse task descriptor value: %s", value)
            return False
    
    def _handle_dnd_time_property(self, value: Any, notify_callback) -> bool:
        """Handle DND/time/charging property (2:51) with state management."""
        from ..const import SCHEDULING_DND_PROPERTY
        
        # Store old values for change detection
        old_dnd_enabled = self._dnd_enabled
        old_dnd_start_time = self._dnd_start_time
        old_dnd_end_time = self._dnd_end_time
        old_timezone = self._timezone
        old_device_time = self._device_time
        
        if self._dnd_time_handler.parse_value(value):
            handler = self._dnd_time_handler
            
            # Handle DND schedule updates
            if handler.payload_type.value == "dnd_schedule":
                self._dnd_enabled = handler.dnd_enabled
                self._dnd_start_time = handler.dnd_start_minute
                self._dnd_end_time = handler.dnd_end_minute
                
                # Sync cleared time sync fields (DND schedule clears time sync state)
                self._timezone = handler.sync_timezone  # Will be None
                self._device_time = handler.sync_timestamp  # Will be None
                
                # Notify changes for backward compatibility
                if old_dnd_enabled != self._dnd_enabled:
                    notify_callback("dnd_enabled", self._dnd_enabled)
                if old_dnd_start_time != self._dnd_start_time:
                    notify_callback("dnd_start_time", self._dnd_start_time)
                if old_dnd_end_time != self._dnd_end_time:
                    notify_callback("dnd_end_time", self._dnd_end_time)
                if old_timezone != self._timezone:
                    notify_callback("timezone", self._timezone)
                if old_device_time != self._device_time:
                    notify_callback("device_time", self._device_time)
                
                # Send scheduling DND notification
                dnd_data = handler.get_dnd_notification_data()
                if dnd_data:
                    notify_callback(SCHEDULING_DND_PROPERTY.name, dnd_data)
                    _LOGGER.debug("DND schedule updated: %s", dnd_data)
            
            # Handle time sync updates
            elif handler.payload_type.value == "time_sync":
                self._device_time = handler.sync_timestamp
                self._timezone = handler.sync_timezone
                
                # Sync cleared DND fields (time sync clears DND state)
                self._dnd_enabled = handler.dnd_enabled  # Will be None
                self._dnd_start_time = handler.dnd_start_minute  # Will be None
                self._dnd_end_time = handler.dnd_end_minute  # Will be None
                
                # Notify changes for backward compatibility
                if old_timezone != self._timezone:
                    notify_callback("timezone", self._timezone)
                if old_device_time != self._device_time:
                    notify_callback("device_time", self._device_time)
                if old_dnd_enabled != self._dnd_enabled:
                    notify_callback("dnd_enabled", self._dnd_enabled)
                if old_dnd_start_time != self._dnd_start_time:
                    notify_callback("dnd_start_time", self._dnd_start_time)
                if old_dnd_end_time != self._dnd_end_time:
                    notify_callback("dnd_end_time", self._dnd_end_time)
                
                # Send scheduling time sync notification
                time_sync_data = handler.get_time_sync_notification_data()
                if time_sync_data:
                    notify_callback(SCHEDULING_TIME_SYNC_PROPERTY_NAME, time_sync_data)
            
            # Handle charging schedule updates
            elif handler.payload_type.value == "charging_schedule":
                # Clear DND and time sync state when charging schedule is received
                self._dnd_enabled = None
                self._dnd_start_time = None
                self._dnd_end_time = None
                self._timezone = None
                self._device_time = None
                
                # Notify changes for backward compatibility
                if old_dnd_enabled is not None:
                    notify_callback("dnd_enabled", None)
                if old_dnd_start_time is not None:
                    notify_callback("dnd_start_time", None)
                if old_dnd_end_time is not None:
                    notify_callback("dnd_end_time", None)
                if old_timezone is not None:
                    notify_callback("timezone", None)
                if old_device_time is not None:
                    notify_callback("device_time", None)
                
                # Send charging schedule notification
                charging_data = handler.get_charging_notification_data()
                if charging_data:
                    notify_callback(SCHEDULING_CHARGING_PROPERTY_NAME, charging_data)
                    _LOGGER.info("Charging schedule updated: %s", charging_data)
            
            # Handle third variant updates
            elif handler.payload_type.value == "third_variant":
                # Clear DND and time sync state when third variant is received
                self._dnd_enabled = None
                self._dnd_start_time = None
                self._dnd_end_time = None
                self._timezone = None
                self._device_time = None
                
                # Notify changes for backward compatibility
                if old_dnd_enabled is not None:
                    notify_callback("dnd_enabled", None)
                if old_dnd_start_time is not None:
                    notify_callback("dnd_start_time", None)
                if old_dnd_end_time is not None:
                    notify_callback("dnd_end_time", None)
                if old_timezone is not None:
                    notify_callback("timezone", None)
                if old_device_time is not None:
                    notify_callback("device_time", None)
                
                # Send third variant notification
                third_variant_data = handler.get_third_variant_notification_data()
                if third_variant_data:
                    notify_callback(SCHEDULING_THIRD_VARIANT_PROPERTY_NAME, third_variant_data)
                    _LOGGER.debug("Property 2:51 third variant notification sent: %s", third_variant_data)
            
            # Handle fourth variant updates
            elif handler.payload_type.value == "fourth_variant":
                # Clear DND and time sync state when fourth variant is received
                self._dnd_enabled = None
                self._dnd_start_time = None
                self._dnd_end_time = None
                self._timezone = None
                self._device_time = None
                
                # Notify changes for backward compatibility
                if old_dnd_enabled is not None:
                    notify_callback("dnd_enabled", None)
                if old_dnd_start_time is not None:
                    notify_callback("dnd_start_time", None)
                if old_dnd_end_time is not None:
                    notify_callback("dnd_end_time", None)
                if old_timezone is not None:
                    notify_callback("timezone", None)
                if old_device_time is not None:
                    notify_callback("device_time", None)
                
                # Send fourth variant notification
                fourth_variant_data = handler.get_fourth_variant_notification_data()
                if fourth_variant_data:
                    notify_callback(SCHEDULING_FOURTH_VARIANT_PROPERTY_NAME, fourth_variant_data)
                    _LOGGER.debug("Property 2:51 fourth variant notification sent: %s", fourth_variant_data)
            
            # Handle fifth variant updates
            elif handler.payload_type.value == "fifth_variant":
                # Clear DND and time sync state when fifth variant is received
                self._dnd_enabled = None
                self._dnd_start_time = None
                self._dnd_end_time = None
                self._timezone = None
                self._device_time = None
                
                # Notify changes for backward compatibility
                if old_dnd_enabled is not None:
                    notify_callback("dnd_enabled", None)
                if old_dnd_start_time is not None:
                    notify_callback("dnd_start_time", None)
                if old_dnd_end_time is not None:
                    notify_callback("dnd_end_time", None)
                if old_timezone is not None:
                    notify_callback("timezone", None)
                if old_device_time is not None:
                    notify_callback("device_time", None)
                
                # Send fifth variant notification
                fifth_variant_data = handler.get_fifth_variant_notification_data()
                if fifth_variant_data:
                    notify_callback(SCHEDULING_FIFTH_VARIANT_PROPERTY_NAME, fifth_variant_data)
                    _LOGGER.debug("Property 2:51 fifth variant notification sent: %s", fifth_variant_data)
            
            # Handle sixth variant updates
            elif handler.payload_type.value == "sixth_variant":
                # Clear DND and time sync state when sixth variant is received
                self._dnd_enabled = None
                self._dnd_start_time = None
                self._dnd_end_time = None
                self._timezone = None
                self._device_time = None
                
                # Notify changes for backward compatibility
                if old_dnd_enabled is not None:
                    notify_callback("dnd_enabled", None)
                if old_dnd_start_time is not None:
                    notify_callback("dnd_start_time", None)
                if old_dnd_end_time is not None:
                    notify_callback("dnd_end_time", None)
                if old_timezone is not None:
                    notify_callback("timezone", None)
                if old_device_time is not None:
                    notify_callback("device_time", None)
                
                # Send sixth variant notification
                sixth_variant_data = handler.get_sixth_variant_notification_data()
                if sixth_variant_data:
                    notify_callback(SCHEDULING_SIXTH_VARIANT_PROPERTY_NAME, sixth_variant_data)
                    _LOGGER.debug("Property 2:51 sixth variant notification sent: %s", sixth_variant_data)
            
            return True
        else:
            return False  # Parsing failed
    
    def _handle_summary_property(self, value: Any, notify_callback) -> bool:
        """Handle mission completion summary (2:52)."""
        from ..const import SCHEDULING_SUMMARY_PROPERTY
        
        if self._summary_handler.parse_value(value):
            summary_data = self._summary_handler.get_notification_data()
            notify_callback(SCHEDULING_SUMMARY_PROPERTY.name, summary_data)
            
            if not self._summary_handler.is_empty:
                _LOGGER.info("Mission completed: %s", summary_data)
            else:
                _LOGGER.debug("Mission completion marker received (empty summary)")
            
            return True
        else:
            _LOGGER.warning("Failed to parse summary value: %s", value)
            return False

    # Device state properties - single source of truth
    @property
    def dnd_enabled(self) -> bool | None:
        """Return Do Not Disturb enabled status."""
        return self._dnd_enabled
    
    @property
    def dnd_start_time(self) -> int | None:
        """Return DND start time in minutes from midnight."""
        return self._dnd_start_time
    
    @property
    def dnd_end_time(self) -> int | None:
        """Return DND end time in minutes from midnight."""
        return self._dnd_end_time
    
    @property
    def timezone(self) -> str | None:
        """Return device timezone."""
        return self._timezone
    
    @property
    def device_time(self) -> str | None:
        """Return device time timestamp."""
        return self._device_time