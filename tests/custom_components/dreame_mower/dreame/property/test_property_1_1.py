"""Tests for Property11Handler class."""

import pytest
from unittest.mock import patch, Mock

from custom_components.dreame_mower.dreame.property.property_1_1 import Property11Handler


class TestProperty11Handler:
    """Test cases for Property11Handler."""

    def test_init(self):
        """Test handler initialization."""
        handler = Property11Handler()
        
        # All properties should be None initially
        assert handler.temperature is None
        assert handler.mode is None
        assert handler.submode is None
        assert handler.battery_raw is None
        assert handler.status_flag is None
        assert handler.phase_marker_hi is None
        assert handler.phase_marker_lo is None
        assert handler.aux_code is None

    def test_parse_value_valid_data(self):
        """Test parsing valid property 1:1 data."""
        handler = Property11Handler()
        
        # Create test data with sentinels (206) and sample payload (18 bytes between sentinels)
        test_data = [
            206,  # Start sentinel (index 0)
            0,    # payload[0] - p0
            0,    # payload[1] - p1
            0,    # payload[2] - p2
            0,    # payload[3] - p3
            0,    # payload[4] - p4
            0,    # payload[5] - p5
            4,    # payload[6] - p6: mode (4=mowing)
            0,    # payload[7] - p7
            0,    # payload[8] - p8
            0,    # payload[9] - p9
            85,   # payload[10] - p10: battery_raw (85%)
            33,   # payload[11] - p11: phase_marker_hi
            35,   # payload[12] - p12: phase_marker_lo
            133,  # payload[13] - p13: submode
            54,   # payload[14] - p14: aux_code
            0,    # payload[15] - p15
            235,  # payload[16] - p16: temperature_raw (23.5°C)
            68,   # payload[17] - p17: status_flag
            206   # End sentinel (index 19)
        ]
        
        result = handler.parse_value(test_data)
        
        # Should return True for successful parsing
        assert result is True
        
        # Check parsed values
        assert handler.mode == 4
        assert handler.battery_raw == 85
        assert handler.phase_marker_hi == 33
        assert handler.phase_marker_lo == 35
        assert handler.submode == 133
        assert handler.aux_code == 54
        assert handler.temperature == 23.5  # 235 / 10.0
        assert handler.status_flag == 68

    def test_parse_value_invalid_length(self):
        """Test parsing with invalid data length."""
        handler = Property11Handler()
        
        # Test with too short data
        result = handler.parse_value([206, 1, 2, 3])
        assert result is False
        
        # Test with too long data
        result = handler.parse_value([206] * 25)
        assert result is False

    def test_parse_value_invalid_type(self):
        """Test parsing with invalid data type."""
        handler = Property11Handler()
        
        # Test with non-list input
        result = handler.parse_value("invalid")
        assert result is False
        
        result = handler.parse_value(None)
        assert result is False
        
        result = handler.parse_value(123)
        assert result is False

    def test_parse_value_invalid_sentinels(self):
        """Test parsing with invalid sentinel values."""
        handler = Property11Handler()
        
        # Test with wrong start sentinel
        test_data = [100] + [0] * 18 + [206]
        result = handler.parse_value(test_data)
        assert result is False
        
        # Test with wrong end sentinel
        test_data = [206] + [0] * 18 + [100]
        result = handler.parse_value(test_data)
        assert result is False
        
        # Test with both wrong sentinels
        test_data = [100] + [0] * 18 + [200]
        result = handler.parse_value(test_data)
        assert result is False

    def test_parse_value_temperature_conversion(self):
        """Test temperature conversion from raw values."""
        handler = Property11Handler()
        
        # Test various temperature values
        test_cases = [
            (0, 0.0),      # 0°C
            (100, 10.0),   # 10°C
            (235, 23.5),   # 23.5°C
            (255, 25.5),   # 25.5°C
            (1, 0.1),      # 0.1°C
        ]
        
        for raw_temp, expected_celsius in test_cases:
            # Create test data with specific temperature value at payload[16] (index 17 in full array)
            test_data = [206] + [0] * 16 + [raw_temp] + [0] + [206]
            
            result = handler.parse_value(test_data)
            assert result is True
            assert handler.temperature == expected_celsius

    def test_parse_value_exception_handling(self):
        """Test exception handling during parsing."""
        handler = Property11Handler()
        
        # Test with data that causes IndexError (valid length but accessing wrong indices)
        with patch('custom_components.dreame_mower.dreame.property.property_1_1.int', side_effect=ValueError("test error")):
            test_data = [206] + [0] * 18 + [206]
            result = handler.parse_value(test_data)
            assert result is False

    def test_parse_value_updates_all_properties(self):
        """Test that parsing updates all internal properties."""
        handler = Property11Handler()
        
        # Set initial values to ensure they get overwritten
        handler._temperature = 99.9
        handler._mode = 99
        handler._submode = 99
        handler._battery_raw = 99
        handler._status_flag = 99
        handler._phase_marker_hi = 99
        handler._phase_marker_lo = 99
        handler._aux_code = 99
        
        # Create test data with specific values (18-byte payload between sentinels)
        test_data = [
            206,  # Start sentinel
            0, 0, 0, 0, 0, 0,  # payload[0-5]
            1,    # payload[6]: mode
            0, 0, 0,  # payload[7-9]
            50,   # payload[10]: battery_raw
            10,   # payload[11]: phase_marker_hi
            20,   # payload[12]: phase_marker_lo
            30,   # payload[13]: submode
            40,   # payload[14]: aux_code
            0,    # payload[15]
            150,  # payload[16]: temperature_raw (15.0°C)
            60,   # payload[17]: status_flag
            206   # End sentinel
        ]
        
        result = handler.parse_value(test_data)
        assert result is True
        
        # All properties should be updated to new values
        assert handler.temperature == 15.0
        assert handler.mode == 1
        assert handler.submode == 30
        assert handler.battery_raw == 50
        assert handler.status_flag == 60
        assert handler.phase_marker_hi == 10
        assert handler.phase_marker_lo == 20
        assert handler.aux_code == 40

    def test_property_getters_return_none_initially(self):
        """Test that all property getters return None before parsing."""
        handler = Property11Handler()
        
        assert handler.temperature is None
        assert handler.mode is None
        assert handler.submode is None
        assert handler.battery_raw is None
        assert handler.status_flag is None
        assert handler.phase_marker_hi is None
        assert handler.phase_marker_lo is None
        assert handler.aux_code is None

    @patch('custom_components.dreame_mower.dreame.property.property_1_1._LOGGER')
    def test_logging_on_invalid_format(self, mock_logger):
        """Test that proper warnings are logged for invalid data format."""
        handler = Property11Handler()
        
        # Test invalid length
        handler.parse_value([1, 2, 3])
        mock_logger.warning.assert_called_with(
            "Property 1:1 invalid format: expected list of 20 integers, got %s", 
            "list"
        )

    @patch('custom_components.dreame_mower.dreame.property.property_1_1._LOGGER')
    def test_logging_on_invalid_sentinels(self, mock_logger):
        """Test that proper warnings are logged for invalid sentinels."""
        handler = Property11Handler()
        
        # Test invalid sentinels
        test_data = [100] + [0] * 18 + [200]
        handler.parse_value(test_data)
        mock_logger.warning.assert_called_with(
            "Property 1:1 invalid sentinels: start=%d, end=%d (expected 206)", 
            100, 200
        )

    @patch('custom_components.dreame_mower.dreame.property.property_1_1._LOGGER')
    def test_logging_on_parsing_error(self, mock_logger):
        """Test that errors are logged when parsing fails."""
        handler = Property11Handler()
        
        # Mock int() to raise an exception
        with patch('custom_components.dreame_mower.dreame.property.property_1_1.int', side_effect=ValueError("test error")):
            test_data = [206] + [0] * 18 + [206]
            handler.parse_value(test_data)
            # Check that error was called (the second argument will be the exception object)
            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args[0]
            assert call_args[0] == "Failed to parse property 1:1: %s"
            assert isinstance(call_args[1], ValueError)

    def test_multiple_parse_calls_update_values(self):
        """Test that multiple parse calls properly update values."""
        handler = Property11Handler()
        
        # First parse
        test_data1 = [206] + [0] * 16 + [100] + [0] + [206]  # 10.0°C
        result1 = handler.parse_value(test_data1)
        assert result1 is True
        assert handler.temperature == 10.0
        
        # Second parse with different value
        test_data2 = [206] + [0] * 16 + [200] + [0] + [206]  # 20.0°C
        result2 = handler.parse_value(test_data2)
        assert result2 is True
        assert handler.temperature == 20.0  # Should be updated