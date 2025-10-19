"""Test minimal sensor entities."""

import pytest
from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dreame_mower.const import DOMAIN
from custom_components.dreame_mower.coordinator import DreameMowerCoordinator
from custom_components.dreame_mower.sensor import (
    DreameMowerBatterySensor,
    DreameMowerStatusSensor,
    DreameMowerChargingStatusSensor,
    DreameMowerChargingScheduleSensor,
    DreameMowerBMSPhaseSensor,
)
from custom_components.dreame_mower.config_flow import (
    CONF_ACCOUNT_TYPE,
    CONF_COUNTRY,
    CONF_MAC,
    CONF_DID,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator for testing."""
    coordinator = MagicMock(spec=DreameMowerCoordinator)
    coordinator.device_connected = True
    coordinator.last_update_success = True
    coordinator.device_mac = "aa:bb:cc:dd:ee:ff"
    coordinator.device_battery_percent = 85  # Default battery level
    coordinator.device_status = "Charging complete"  # Default status
    coordinator.device_charging_status = "Charging"  # Default charging status
    coordinator.device_bms_phase = 5  # Default BMS phase
    return coordinator


@pytest.fixture
def device_id():
    """Return a test device ID."""
    return "test_device_123"


async def test_battery_sensor_initialization(mock_coordinator, device_id):
    """Test battery sensor initialization."""
    sensor = DreameMowerBatterySensor(mock_coordinator)
    
    assert sensor.coordinator == mock_coordinator
    assert sensor._entity_description_key == "battery"
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff_battery"


async def test_battery_sensor_native_value_available(mock_coordinator, device_id):
    """Test battery sensor returns value when available."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    
    # Configure the mock to return the battery percentage
    mock_coordinator.device_battery_percent = 85
    
    sensor = DreameMowerBatterySensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value == 85


async def test_battery_sensor_native_value_unavailable(mock_coordinator, device_id):
    """Test battery sensor returns None when unavailable."""
    mock_coordinator.device_connected = False
    mock_coordinator.last_update_success = False
    
    # Configure the mock to return None for battery percentage
    mock_coordinator.device_battery_percent = None
    
    sensor = DreameMowerBatterySensor(mock_coordinator)
    
    assert sensor.available is False
    assert sensor.native_value is None


async def test_status_sensor_initialization(mock_coordinator, device_id):
    """Test status sensor initialization."""
    sensor = DreameMowerStatusSensor(mock_coordinator)
    
    assert sensor.coordinator == mock_coordinator
    assert sensor._entity_description_key == "status"
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff_status"


async def test_status_sensor_native_value_available(mock_coordinator, device_id):
    """Test status sensor returns status when available."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    
    sensor = DreameMowerStatusSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value == "Charging complete"


async def test_status_sensor_native_value_unavailable(mock_coordinator, device_id):
    """Test status sensor returns offline when unavailable."""
    mock_coordinator.device_connected = False
    mock_coordinator.last_update_success = False
    
    sensor = DreameMowerStatusSensor(mock_coordinator)
    
    assert sensor.available is False
    assert sensor.native_value == "offline"


async def test_charging_status_sensor_initialization(mock_coordinator, device_id):
    """Test charging status sensor initialization."""
    sensor = DreameMowerChargingStatusSensor(mock_coordinator)
    
    assert sensor.coordinator == mock_coordinator
    assert sensor._entity_description_key == "charging_status"
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff_charging_status"


async def test_charging_status_sensor_native_value_available(mock_coordinator, device_id):
    """Test charging status sensor returns value when available."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    
    mock_coordinator.device_charging_status = "Charging"
    
    sensor = DreameMowerChargingStatusSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value == "Charging"


async def test_charging_status_sensor_native_value_unavailable(mock_coordinator, device_id):
    """Test charging status sensor returns None when unavailable."""
    mock_coordinator.device_connected = False
    mock_coordinator.last_update_success = False
    
    mock_coordinator.device_charging_status = None
    
    sensor = DreameMowerChargingStatusSensor(mock_coordinator)
    
    assert sensor.available is False
    assert sensor.native_value is None


async def test_bms_phase_sensor_initialization(mock_coordinator, device_id):
    """Test BMS phase sensor initialization."""
    sensor = DreameMowerBMSPhaseSensor(mock_coordinator)
    
    assert sensor.coordinator == mock_coordinator
    assert sensor._entity_description_key == "bms_phase"
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff_bms_phase"


async def test_bms_phase_sensor_native_value_available(mock_coordinator, device_id):
    """Test BMS phase sensor returns value when available."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    
    mock_coordinator.device_bms_phase = 7
    
    sensor = DreameMowerBMSPhaseSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value == 7


async def test_bms_phase_sensor_native_value_unavailable(mock_coordinator, device_id):
    """Test BMS phase sensor returns None when unavailable."""
    mock_coordinator.device_connected = False
    mock_coordinator.last_update_success = False
    
    mock_coordinator.device_bms_phase = None
    
    sensor = DreameMowerBMSPhaseSensor(mock_coordinator)
    
    assert sensor.available is False
    assert sensor.native_value is None


async def test_charging_schedule_sensor_initialization(mock_coordinator, device_id):
    """Test charging schedule sensor initialization."""
    sensor = DreameMowerChargingScheduleSensor(mock_coordinator)
    
    assert sensor.coordinator == mock_coordinator
    assert sensor._entity_description_key == "charging_schedule"
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff_charging_schedule"


async def test_charging_schedule_sensor_no_schedule(mock_coordinator, device_id):
    """Test charging schedule sensor when no schedule is available."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    mock_coordinator.current_charging_schedule_data = None
    
    sensor = DreameMowerChargingScheduleSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value is None
    
    attributes = sensor.extra_state_attributes
    assert attributes == {}


async def test_charging_schedule_sensor_disabled(mock_coordinator, device_id):
    """Test charging schedule sensor when schedule is disabled."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    mock_coordinator.current_charging_schedule_data = {
        "enabled": False,
        "auto_recharge_percent": 15,
        "resume_percent": 95,
        "start_minute": 1080,  # 18:00
        "end_minute": 480,     # 08:00
    }
    
    sensor = DreameMowerChargingScheduleSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value is False
    
    attributes = sensor.extra_state_attributes
    assert attributes["enabled"] is False
    assert attributes["auto_recharge_percent"] == 15
    assert attributes["resume_percent"] == 95
    assert attributes["start_time"] == "18:00"
    assert attributes["end_time"] == "08:00"


async def test_charging_schedule_sensor_enabled(mock_coordinator, device_id):
    """Test charging schedule sensor when schedule is enabled."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    mock_coordinator.current_charging_schedule_data = {
        "enabled": True,
        "auto_recharge_percent": 20,
        "resume_percent": 80,
        "start_minute": 480,   # 08:00
        "end_minute": 1080,    # 18:00
    }
    
    sensor = DreameMowerChargingScheduleSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value is True
    
    attributes = sensor.extra_state_attributes
    assert attributes["enabled"] is True
    assert attributes["auto_recharge_percent"] == 20
    assert attributes["resume_percent"] == 80
    assert attributes["start_time"] == "08:00"
    assert attributes["end_time"] == "18:00"


async def test_charging_schedule_sensor_enabled_partial_data(mock_coordinator, device_id):
    """Test charging schedule sensor when enabled but missing time data."""
    mock_coordinator.device_connected = True
    mock_coordinator.last_update_success = True
    mock_coordinator.current_charging_schedule_data = {
        "enabled": True,
        "auto_recharge_percent": 15,
        "resume_percent": 95,
        # Missing start_minute and end_minute
    }
    
    sensor = DreameMowerChargingScheduleSensor(mock_coordinator)
    
    assert sensor.available is True
    assert sensor.native_value is True
    
    attributes = sensor.extra_state_attributes
    assert attributes["enabled"] is True
    assert attributes["auto_recharge_percent"] == 15
    assert attributes["resume_percent"] == 95
    assert attributes["start_time"] is None
    assert attributes["end_time"] is None


async def test_charging_schedule_sensor_format_time_minutes():
    """Test the time formatting helper function."""
    sensor = DreameMowerChargingScheduleSensor(MagicMock())
    
    # Test various time values
    assert sensor._format_time_minutes(0) == "00:00"     # Midnight
    assert sensor._format_time_minutes(60) == "01:00"    # 1 AM
    assert sensor._format_time_minutes(480) == "08:00"   # 8 AM
    assert sensor._format_time_minutes(720) == "12:00"   # Noon
    assert sensor._format_time_minutes(1080) == "18:00"  # 6 PM
    assert sensor._format_time_minutes(1439) == "23:59"  # 11:59 PM
    assert sensor._format_time_minutes(795) == "13:15"   # 1:15 PM
    assert sensor._format_time_minutes(858) == "14:18"   # 2:18 PM
