"""Basic tests for the DreameMowerDevice class."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch, PropertyMock

from custom_components.dreame_mower.dreame.device import DreameMowerDevice


class MockCloudDevice:
    """Mock cloud device for testing."""
    
    def __init__(self):
        self._connected = False
        self._message_callback = None
        self._connected_callback = None
        self._disconnected_callback = None
        self.device_id = "test_device_123"  # Add device_id for execute_action method
    
    @property
    def connected(self) -> bool:
        """Mock connected property (read-only like the real implementation)."""
        return self._connected
    
    def connect(self, message_callback=None, connected_callback=None, disconnected_callback=None):
        self._message_callback = message_callback
        self._connected_callback = connected_callback
        self._disconnected_callback = disconnected_callback
        self._connected = True
        
        # Simulate connection callback
        if self._connected_callback:
            self._connected_callback()
        
        return True
    
    def disconnect(self):
        self._connected = False
        
        # Simulate disconnection callback
        if self._disconnected_callback:
            self._disconnected_callback()
    
    def get_device_info(self):
        """Mock device info from devices_list endpoint."""
        return {
            "battery": 90,
            "latestStatus": 13,  # Charging complete
            "ver": "1.5.0_test",
            "sn": "TEST123456",
            "mac": "AA:BB:CC:DD:EE:FF",
            "online": True
        }
    
    def simulate_message(self, message):
        """Helper method to simulate incoming messages for testing."""
        if self._message_callback:
            self._message_callback(message)
    
    def set_connected_state(self, connected: bool):
        """Helper method for tests to manually set connection state."""
        self._connected = connected

    def get_file_download_url(self, file_path: str) -> str | None:
        """Mock file download URL getter for testing."""
        # Return a mock URL for testing
        return f"https://mock.test.com/download/{file_path}"

    def action(self, siid: int, aiid: int, parameters=None, retry_count: int = 2):
        """Mock action call; return a boolean to indicate success."""
        # For tests we just return True to indicate success
        return True

    def execute_action(self, action) -> bool:
        """Mock execute_action method that uses action internally."""
        if not self.connected:
            return False
        return self.action(action.siid, action.aiid)


@pytest.fixture
def device():
    """Create a basic device instance for testing."""
    with patch('custom_components.dreame_mower.dreame.device.DreameMowerCloudDevice') as mock_cloud_device_class:
        with patch('custom_components.dreame_mower.dreame.utils.requests') as mock_requests:
            with patch('custom_components.dreame_mower.dreame.utils.os.makedirs') as mock_makedirs:
                with patch('builtins.open', create=True) as mock_open:
                    # Setup requests mock
                    mock_response = Mock()
                    mock_response.text = '{"mock": "data"}'
                    mock_response.content = b'{"mock": "data"}'
                    mock_response.ok = True
                    mock_response.raise_for_status.return_value = None
                    mock_requests.get.return_value = mock_response
                    
                    # Setup file operations mocks
                    mock_makedirs.return_value = None
                    mock_file = Mock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    mock_cloud_device = MockCloudDevice()
                    mock_cloud_device_class.return_value = mock_cloud_device
                    
                    device = DreameMowerDevice(
                        device_id="test_device_123",
                        username="test_user",
                        password="test_password",
                        account_type="dreame",
                        country="DE",
                        hass_config_dir="/tmp/test_config"
                    )
                    
                    # Ensure the mock is properly attached
                    device._cloud_device = mock_cloud_device
                    
                    return device


def test_device_initialization(device):
    """Test basic device initialization."""
    assert device.device_id == "test_device_123"
    assert device.username == "test_user"
    assert device.connected is False
    assert device.firmware == "Unknown"
    assert isinstance(device.last_update, datetime)


def test_device_properties(device):
    """Test device property access."""
    # Test initial state
    assert not device.connected
    assert device.firmware == "Unknown"
    
    # Test property updates
    device._firmware = "1.2.3"
    
    # Test connected property after mocking connection
    device._cloud_device.set_connected_state(True)
    assert device.connected is True
    
    assert device.firmware == "1.2.3"


def test_register_property_callback(device):
    """Test property callback registration."""
    callback_called = []
    
    def test_callback(prop_name, value):
        callback_called.append((prop_name, value))
    
    device.register_property_callback(test_callback)
    device._notify_property_change("test_prop", "test_value")
    
    assert len(callback_called) == 1
    assert callback_called[0] == ("test_prop", "test_value")


@pytest.mark.asyncio
async def test_connect(device):
    """Test device connection."""
    # Manually set connected state for mock
    device._cloud_device.set_connected_state(True)
    
    result = await device.connect()
    
    assert result is True
    assert device.connected is True


@pytest.mark.asyncio
async def test_disconnect(device):
    """Test device disconnection."""
    # First connect
    device._cloud_device.set_connected_state(True)
    await device.connect()
    assert device.connected is True
    
    # Then disconnect
    await device.disconnect()
    # Note: disconnect doesn't change mock connected state in current implementation
    # This tests the disconnect method runs without errors


@pytest.mark.asyncio
async def test_start_mowing_when_connected(device):
    """Test start mowing when device is connected."""
    device._cloud_device.set_connected_state(True)
    await device.connect()
    
    result = await device.start_mowing()
    assert result is True


@pytest.mark.asyncio
async def test_start_mowing_when_disconnected(device):
    """Test start mowing when device is disconnected."""
    result = await device.start_mowing()
    assert result is False


@pytest.mark.asyncio
async def test_pause_when_connected(device):
    """Test pause when device is connected."""
    device._cloud_device.set_connected_state(True)
    await device.connect()
    
    result = await device.pause()
    assert result is True


@pytest.mark.asyncio
async def test_pause_when_disconnected(device):
    """Test pause when device is disconnected."""
    result = await device.pause()
    assert result is False


@pytest.mark.asyncio
async def test_return_to_dock_when_connected(device):
    """Test return to dock when device is connected."""
    device._cloud_device.set_connected_state(True)
    await device.connect()
    
    # Patch the internal mission_completed_event.wait coroutine so the
    # return_to_dock sequence does not actually wait up to 30 seconds.
    # (Patching asyncio.wait_for directly previously caused an un-awaited
    # Event.wait() coroutine warning when raising TimeoutError immediately.)
    with patch.object(device._mission_completed_event, "wait", new=AsyncMock(return_value=True)):
        result = await device.return_to_dock()
        assert result is True


@pytest.mark.asyncio
async def test_return_to_dock_when_disconnected(device):
    """Test return to dock when device is disconnected."""
    result = await device.return_to_dock()
    assert result is False


@pytest.mark.asyncio
async def test_message_callback(device):
    """Test handling of incoming messages."""
    # Connect device - this will fetch initial device info
    device._cloud_device.set_connected_state(True)
    await device.connect()
    
    # Check that initial device info was loaded
    assert device.firmware == "1.5.0_test"  # From mock get_device_info
    assert device.battery_percent == 90  # From mock get_device_info
    assert device.status == "charging_complete"  # From mock latestStatus 13
    
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    # Test MQTT message with properties_changed format (battery update)
    battery_message = {
        "id": 123,
        "method": "properties_changed",
        "params": [
            {
                "did": "test_device_123",
                "siid": 3,
                "piid": 1,
                "value": 75
            }
        ]
    }
    
    # Simulate MQTT message
    device._cloud_device.simulate_message(battery_message)
    
    # Check battery was updated via MQTT
    assert device.battery_percent == 75
    
    # Check property change notifications
    assert ("battery_percent", 75) in property_changes


def test_service1_session_start_properties():
    """Test handling of Service1 session start properties 1:50 and 1:51."""
    device = DreameMowerDevice(
        device_id="test_device_123",
        username="test_user", 
        password="test_password",
        account_type="dreame",
        country="DE",
        hass_config_dir="/tmp/test_config"
    )
    property_changes = []
    
    def property_change_callback(property_name, value):
        property_changes.append((property_name, value))
    
    device.register_property_callback(property_change_callback)
    
    # Initial state should be False
    assert device.service1_property_50 is False
    assert device.service1_property_51 is False
    assert device.service1_completion_flag is False
    
    # Simulate the exact MQTT messages from logs
    message_property_50 = {
        'id': 305, 
        'method': 'properties_changed', 
        'params': [{'did': '-1******95', 'piid': 50, 'siid': 1}]
    }
    
    message_property_51 = {
        'id': 306, 
        'method': 'properties_changed', 
        'params': [{'did': '-1******95', 'piid': 51, 'siid': 1}]
    }
    
    # Test property 50 handling
    device._handle_message(message_property_50)
    assert device.service1_property_50 is True
    assert ("service1_property_50", True) in property_changes
    
    # Test property 51 handling 
    device._handle_message(message_property_51)
    assert device.service1_property_51 is True
    assert ("service1_property_51", True) in property_changes
    
    # Verify completion flag is still False (different property)
    assert device.service1_completion_flag is False


def test_handle_mqtt_props_success(device):
    """Test _handle_mqtt_props with known parameter (success case)."""
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    # Test handling ota_state parameter
    assert device._handle_mqtt_props({"ota_state": "idle"}) is True
    assert device.ota_state == "idle"
    assert ("ota_state", "idle") in property_changes


def test_handle_mqtt_props_failure(device):
    """Test _handle_mqtt_props with unknown parameters (failure case).""" 
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    assert device._handle_mqtt_props({"unknown_param": "some_value"}) is False
    assert len(property_changes) == 0


def test_service2_property_62_handling(device):
    """Test Service 2 property 62 (2:62) handling."""
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    # Test the specific message structure
    message = {"siid": 2, "piid": 62, "value": 0}
    
    assert device._handle_mqtt_property_update(message) is True
    assert ("service2_property_62", 0) in property_changes


def test_service2_property_64_handling(device):
    """Test Service 2 property 64 (2:64) work statistics handling."""
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    # Test with a simplified version of the complex work statistics structure
    # from the issue report
    message = {
        "siid": 2, 
        "piid": 64, 
        "value": {
            "cw": {
                "cy": {
                    "ci": ["0.0", "0.0", "0.0", "0.0"],
                    "ct": "2025-10-02 12:27:17",
                    "p": ["0.0"] * 120  # Simplified array
                },
                "ow": {
                    "ci": ["801"],
                    "ct": "2025-10-02 12:27:17"
                }
            },
            "fw": {
                "xz": {
                    "bi": [],
                    "bt": "",
                    "fi": [0] * 48,
                    "wt": "2025-09-30T00:00:00+00:00"
                }
            },
            "p": [9.9, 53.6],
            "rt": "",
            "tz": "Europe/Berlin",
            "wr": "2025-10-02 12:22:56",
            "ws": "2025-10-02 12:27:15"
        }
    }
    
    assert device._handle_mqtt_property_update(message) is True
    # Verify the property change was notified
    assert any(name == "service2_property_64" for name, _ in property_changes)
    # Verify the value was passed through
    notified_value = next(value for name, value in property_changes if name == "service2_property_64")
    assert isinstance(notified_value, dict)
    assert "cw" in notified_value
    assert "fw" in notified_value


def test_service5_property_104_handling(device):
    """Test Service 5 property 104 (5:104) handling from issue #1616."""
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    # Test with value 7 (Task incomplete - spot mowing)
    message = {
        "siid": 5, 
        "piid": 104, 
        "value": 7
    }
    
    assert device._handle_mqtt_property_update(message) is True
    
    # Verify the property change was notified with new property name
    assert any(name == "task_status" for name, _ in property_changes)
    
    # Verify the value was passed through correctly
    notified_value = next(value for name, value in property_changes if name == "task_status")
    assert isinstance(notified_value, dict)
    assert "status_code" in notified_value
    assert notified_value["status_code"] == 7
    assert "status_description" in notified_value
    assert notified_value["status_description"] == "Task incomplete - spot mowing"
    
    # Also check that the individual state change notification was sent
    assert any(name == "task_status_code" for name, _ in property_changes)
    individual_value = next(value for name, value in property_changes if name == "task_status_code")
    assert individual_value == 7


def test_service5_property_104_unknown_value(device):
    """Test Service 5 property 104 (5:104) with unknown value from issue #1616."""
    # Track property changes
    property_changes = []
    def track_changes(prop_name, value):
        property_changes.append((prop_name, value))
    
    device.register_property_callback(track_changes)
    
    # Test with unknown value 13 (from original issue #1616)
    # Unknown values should still be handled with generic description
    message = {
        "siid": 5, 
        "piid": 104, 
        "value": 13
    }
    
    # Should return True - we handle it even if we don't know what it means yet
    assert device._handle_mqtt_property_update(message) is True
    
    # Should send notifications with generic "Unknown" description
    assert any(name == "task_status" for name, _ in property_changes)
    notified_value = next(value for name, value in property_changes if name == "task_status")
    assert notified_value["status_code"] == 13
    assert notified_value["status_description"] == "Unknown task status: 13"


def test_firmware_install_state_handling():
    """Test firmware installation state property (1:2) handling."""
    device = DreameMowerDevice(
        device_id="test_device_123",
        username="test_user",
        password="test_password",
        account_type="dreame",
        country="DE",
        hass_config_dir="/tmp/test_config"
    )
    property_changes = []
    
    def property_change_callback(property_name, value):
        property_changes.append((property_name, value))
    
    device.register_property_callback(property_change_callback)
    
    # Initial state should be None
    assert device.firmware_install_state is None
    
    # Test valid value 2
    message_value_2 = {
        'id': 104,
        'method': 'properties_changed',
        'params': [{'did': '-1******18', 'piid': 2, 'siid': 1, 'value': 2}]
    }
    device._handle_message(message_value_2)
    assert device.firmware_install_state == 2
    assert ("firmware_install_state", 2) in property_changes
    
    # Test valid value 3 (from the issue)
    message_value_3 = {
        'id': 105,
        'method': 'properties_changed',
        'params': [{'did': '-1******18', 'piid': 2, 'siid': 1, 'value': 3}]
    }
    device._handle_message(message_value_3)
    assert device.firmware_install_state == 3
    assert ("firmware_install_state", 3) in property_changes
    
    # Test invalid value - should be rejected
    property_changes.clear()
    message_invalid = {"siid": 1, "piid": 2, "value": 99}
    result = device._handle_mqtt_property_update(message_invalid)
    assert result is False  # Invalid value should return False
    assert device.firmware_install_state == 3  # State should remain unchanged
    assert len(property_changes) == 0  # No property change notification for invalid value


def test_firmware_download_progress_handling():
    """Test firmware download progress property (1:3) handling."""
    device = DreameMowerDevice(
        device_id="test_device_123",
        username="test_user",
        password="test_password",
        account_type="dreame",
        country="DE",
        hass_config_dir="/tmp/test_config"
    )
    property_changes = []
    
    def property_change_callback(property_name, value):
        property_changes.append((property_name, value))
    
    device.register_property_callback(property_change_callback)
    
    # Initial state should be None
    assert device.firmware_download_progress is None
    
    # Test progress values from the issue (1 to 100)
    test_values = [1, 8, 14, 18, 23, 28, 33, 38, 42, 45, 47, 49, 53, 57, 61, 66, 72, 79, 87, 93, 98, 100]
    
    for progress in test_values:
        message = {
            'id': 132 + progress,
            'method': 'properties_changed',
            'params': [{'did': '-1******96', 'piid': 3, 'siid': 1, 'value': progress}]
        }
        device._handle_message(message)
        assert device.firmware_download_progress == progress
        assert ("firmware_download_progress", progress) in property_changes
    
    # Test edge cases
    # Test 0% (edge case)
    property_changes.clear()
    message_zero = {"siid": 1, "piid": 3, "value": 0}
    result = device._handle_mqtt_property_update(message_zero)
    assert result is True
    assert device.firmware_download_progress == 0
    assert ("firmware_download_progress", 0) in property_changes
    
    # Test invalid negative value - should be rejected
    property_changes.clear()
    message_negative = {"siid": 1, "piid": 3, "value": -1}
    result = device._handle_mqtt_property_update(message_negative)
    assert result is False  # Invalid value should return False
    assert device.firmware_download_progress == 0  # State should remain unchanged
    assert len(property_changes) == 0  # No property change notification for invalid value
    
    # Test invalid value > 100 - should be rejected
    property_changes.clear()
    message_over_100 = {"siid": 1, "piid": 3, "value": 101}
    result = device._handle_mqtt_property_update(message_over_100)
    assert result is False  # Invalid value should return False
    assert device.firmware_download_progress == 0  # State should remain unchanged
    assert len(property_changes) == 0  # No property change notification for invalid value


def test_firmware_validation_event_handling():
    """Test firmware validation event (1:1) handling."""
    device = DreameMowerDevice(
        device_id="test_device_123",
        username="test_user",
        password="test_password",
        account_type="dreame",
        country="DE",
        hass_config_dir="/tmp/test_config"
    )
    property_changes = []
    
    def property_change_callback(property_name, value):
        property_changes.append((property_name, value))
    
    device.register_property_callback(property_change_callback)
    
    # Test firmware validation event message from the issue
    message = {
        'id': 158,
        'method': 'event_occured',
        'params': {'did': '-1******18', 'eiid': 1, 'siid': 1}
    }
    
    device._handle_message(message)
    
    # Check that event was handled and notification was sent
    firmware_validation_changes = [change for change in property_changes if change[0] == "firmware_validation"]
    assert len(firmware_validation_changes) == 1
    
    # Verify notification data structure
    event_data = firmware_validation_changes[0][1]
    assert event_data["siid"] == 1
    assert event_data["eiid"] == 1
    assert "timestamp" in event_data


def test_service2_property_63_handling():
    """Test Service 2 property 63 (2:63) handling - observed in issue #134."""
    device = DreameMowerDevice(
        device_id="test_device_123",
        username="test_user",
        password="test_password",
        account_type="dreame",
        country="DE",
        hass_config_dir="/tmp/test_config"
    )
    property_changes = []
    
    def property_change_callback(property_name, value):
        property_changes.append((property_name, value))
    
    device.register_property_callback(property_change_callback)
    
    # Test the message from issue #134 with value -33001
    message = {
        'id': 107,
        'method': 'properties_changed',
        'params': [{'did': '-1******73', 'piid': 63, 'siid': 2, 'value': -33001}]
    }
    
    # This should return False to enable crowdsourcing
    device._handle_message(message)
    
    # Verify that no property change notification was sent (returns False for crowdsourcing)
    service2_63_changes = [change for change in property_changes if change[0] == "service2_property_63"]
    assert len(service2_63_changes) == 0  # Should not notify since we return False
