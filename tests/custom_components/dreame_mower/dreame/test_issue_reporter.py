"""Tests for DreameMowerIssueReporter."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import urllib.parse

from custom_components.dreame_mower.dreame.issue_reporter import DreameMowerIssueReporter


@pytest.fixture
def hass():
    """Mock Home Assistant instance."""
    mock_hass = MagicMock()
    mock_hass.services = MagicMock()
    mock_hass.services.async_call = AsyncMock()
    return mock_hass


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance (alias for hass)."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def issue_reporter(hass):
    """Create issue reporter instance."""
    return DreameMowerIssueReporter(hass)


class TestIssueReporter:
    """Test issue reporter functionality."""
    
    @pytest.mark.asyncio
    async def test_create_github_issue_url_with_event_time(self, issue_reporter):
        """Test that GitHub issue URL includes event time when provided."""
        # Arrange
        message_type = "message"
        raw_message = {
            "id": 1467,
            "method": "properties_changed",
            "params": [{"did": "-1234567890", "piid": 108, "siid": 5, "value": 1}]
        }
        device_model = "mova.mower.g2405a"
        device_firmware = "4.3.6_0430"
        integration_version = "0.1.8"
        event_time = "2025-10-12T17:23:45.123456"
        
        # Act
        url = issue_reporter._create_github_issue_url(
            message_type,
            raw_message,
            device_model,
            device_firmware,
            integration_version,
            event_time
        )
        
        # Assert
        assert "github.com/antondaubert/dreame-mower/issues/new?" in url
        
        # Parse the URL query parameters
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Check the issue body contains event time
        issue_body = query_params['body'][0]
        assert event_time in issue_body
        assert "**Event Time:**" in issue_body
        
        # Check that device IDs are anonymized
        assert "-1234567890" not in issue_body
        assert "-1*******90" in issue_body
    
    @pytest.mark.asyncio
    async def test_create_github_issue_url_without_event_time(self, issue_reporter):
        """Test that GitHub issue URL works without event time."""
        # Arrange
        message_type = "message"
        raw_message = {"id": 123, "method": "test"}
        device_model = "test.model"
        device_firmware = "1.0.0"
        integration_version = "0.1.0"
        
        # Act
        url = issue_reporter._create_github_issue_url(
            message_type,
            raw_message,
            device_model,
            device_firmware,
            integration_version,
            event_time=None
        )
        
        # Assert
        assert "github.com/antondaubert/dreame-mower/issues/new?" in url
        
        # Parse the URL query parameters
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Check the issue body does not contain event time section
        issue_body = query_params['body'][0]
        assert "**Event Time:**" not in issue_body
    
    @pytest.mark.asyncio
    async def test_create_unhandled_mqtt_notification_with_event_time(self, hass, issue_reporter):
        """Test notification creation with event time in mqtt_data."""
        # Arrange
        event_time = datetime.now().isoformat()
        mqtt_data = {
            "type": "message",
            "raw_message": {
                "id": 1467,
                "method": "properties_changed",
                "params": [{"did": "-1234567890", "piid": 108, "siid": 5, "value": 1}]
            },
            "event_time": event_time
        }
        device_model = "mova.mower.g2405a"
        device_firmware = "4.3.6_0430"
        
        # Mock the integration version retrieval
        with patch.object(issue_reporter, '_get_integration_version', new=AsyncMock(return_value="0.1.8")):
            # Act
            await issue_reporter.create_unhandled_mqtt_notification(
                mqtt_data,
                device_model,
                device_firmware
            )
        
        # Assert
        # Verify that async_call was called with the notification
        assert hass.services.async_call.called
        call_args = hass.services.async_call.call_args
        assert call_args[0][0] == "persistent_notification"
        assert call_args[0][1] == "create"
        
        # The notification data is the third positional argument
        notification_data = call_args[0][2]
        assert "notification_id" in notification_data
        assert "title" in notification_data
        assert "message" in notification_data


class TestNotificationTracking:
    """Test notification tracking functionality."""

    def test_track_notification(self, issue_reporter):
        """Test that notifications are tracked correctly."""
        # Track a notification
        issue_reporter._track_notification("Error", "Blade Error", "Blades are stuck")
        
        # Verify it's in the recent notifications
        assert len(issue_reporter.recent_notifications) == 1
        
        notification = issue_reporter.recent_notifications[0]
        assert notification["type"] == "Error"
        assert notification["title"] == "Blade Error"
        assert notification["description"] == "Blades are stuck"
        assert "timestamp" in notification

    def test_track_multiple_notifications(self, issue_reporter):
        """Test tracking multiple notifications."""
        # Track several notifications
        issue_reporter._track_notification("Error", "Error 1", "Description 1")
        issue_reporter._track_notification("Info", "Info 1", "Description 2")
        issue_reporter._track_notification("Warning", "Warning 1", "Description 3")
        
        # Verify all are tracked (most recent first)
        assert len(issue_reporter.recent_notifications) == 3
        assert issue_reporter.recent_notifications[0]["title"] == "Warning 1"
        assert issue_reporter.recent_notifications[1]["title"] == "Info 1"
        assert issue_reporter.recent_notifications[2]["title"] == "Error 1"

    def test_max_notifications_limit(self, issue_reporter):
        """Test that only last 5 notifications are kept."""
        # Track 7 notifications
        for i in range(7):
            issue_reporter._track_notification("Info", f"Notification {i}", f"Description {i}")
        
        # Verify only last 5 are kept
        assert len(issue_reporter.recent_notifications) == 5
        
        # Verify they are the most recent ones (6, 5, 4, 3, 2)
        assert issue_reporter.recent_notifications[0]["title"] == "Notification 6"
        assert issue_reporter.recent_notifications[4]["title"] == "Notification 2"

    def test_get_recent_notifications_context_empty(self, issue_reporter):
        """Test getting context when no notifications exist."""
        context = issue_reporter._get_recent_notifications_context()
        assert context == "No recent notifications"

    def test_get_recent_notifications_context_with_data(self, issue_reporter):
        """Test getting formatted context with notifications."""
        # Track some notifications
        issue_reporter._track_notification("Error", "Blade Error", "Blades are stuck")
        issue_reporter._track_notification("Info", "Docked", "Mower returned to dock")
        
        context = issue_reporter._get_recent_notifications_context()
        
        # Verify format includes all expected elements
        assert "1. **[" in context  # First entry
        assert "2. **[" in context  # Second entry
        assert "Error: Blade Error" in context
        assert "Blades are stuck" in context
        assert "Info: Docked" in context
        assert "Mower returned to dock" in context

    def test_github_issue_includes_context(self, issue_reporter):
        """Test that GitHub issue URL includes recent notifications."""
        # Track some notifications
        issue_reporter._track_notification("Error", "Test Error", "Test Description")
        
        # Create GitHub issue URL
        url = issue_reporter._create_github_issue_url(
            message_type="property",
            raw_message={"siid": 5, "piid": 3, "value": 42},
            device_model="A1",
            device_firmware="1.0.0",
            integration_version="0.2.2",
            event_time="2025-10-14T12:00:00"
        )
        
        # Verify URL contains recent notifications context
        assert "github.com" in url
        # The context is URL encoded, so check for key parts
        assert "Recent" in url or "recent" in url.lower()

    @pytest.mark.asyncio
    async def test_error_notification_tracked(self, issue_reporter, mock_hass):
        """Test that error notifications are tracked."""
        await issue_reporter.create_device_error_notification(
            code=28,
            name="Blade Error",
            description="Blades are stuck",
            device_model="A1",
            device_firmware="1.0.0"
        )
        
        # Verify notification was tracked
        assert len(issue_reporter.recent_notifications) == 1
        notification = issue_reporter.recent_notifications[0]
        assert notification["type"] == "Error"
        assert notification["title"] == "Blade Error"
        assert notification["description"] == "Blades are stuck"

    @pytest.mark.asyncio
    async def test_info_notification_tracked(self, issue_reporter, mock_hass):
        """Test that info notifications are tracked."""
        await issue_reporter.create_device_info_notification(
            code=1,
            name="Docked",
            description="Mower is docked",
            device_model="A1",
            device_firmware="1.0.0"
        )
        
        # Verify notification was tracked
        assert len(issue_reporter.recent_notifications) == 1
        notification = issue_reporter.recent_notifications[0]
        assert notification["type"] == "Info"
        assert notification["title"] == "Docked"
        assert notification["description"] == "Mower is docked"

    @pytest.mark.asyncio
    async def test_mqtt_discovery_tracked(self, issue_reporter, mock_hass):
        """Test that MQTT discovery events are tracked with timestamp."""
        # Mock integration version
        with patch.object(issue_reporter, '_get_integration_version', return_value="0.2.2"):
            await issue_reporter.create_unhandled_mqtt_notification(
                mqtt_data={
                    "type": "property",
                    "siid": 5,
                    "piid": 3,
                    "value": 42,
                    "raw_message": {"siid": 5, "piid": 3, "value": 42},
                    "event_time": "2025-10-14T12:00:00"
                },
                device_model="A1",
                device_firmware="1.0.0"
            )
        
        # Verify discovery event was tracked
        assert len(issue_reporter.recent_notifications) == 1
        notification = issue_reporter.recent_notifications[0]
        assert notification["type"] == "Discovery"
        assert "MQTT Discovery" in notification["title"]
        assert "siid:5 piid:3" in notification["title"]
        assert "42" in notification["description"]
        assert "timestamp" in notification
