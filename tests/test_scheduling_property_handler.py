"""Test the scheduling property handler."""

import pytest
from unittest.mock import Mock

from custom_components.dreame_mower.dreame.const import (
    SCHEDULING_TASK_PROPERTY,
    SCHEDULING_DND_PROPERTY,
    SCHEDULING_SUMMARY_PROPERTY,
)
from custom_components.dreame_mower.dreame.property.scheduling import (
    SchedulingPropertyHandler,
    TaskHandler,
    DndTimeHandler,
    ChargingHandler,
    ThirdVariantHandler,
    FourthVariantHandler,
    FifthVariantHandler,
    SixthVariantHandler,
    SummaryHandler,
    TaskType,
    Property51Type,
    SCHEDULING_TIME_SYNC_PROPERTY_NAME,
    SCHEDULING_CHARGING_PROPERTY_NAME,
    SCHEDULING_THIRD_VARIANT_PROPERTY_NAME,
    SCHEDULING_FOURTH_VARIANT_PROPERTY_NAME,
    SCHEDULING_FIFTH_VARIANT_PROPERTY_NAME,
    SCHEDULING_SIXTH_VARIANT_PROPERTY_NAME,
)


class TestTaskHandler:
    """Test TaskHandler for property 2:50."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = TaskHandler()

    def test_parse_task_string_literal(self):
        """Test parsing task descriptor from string literal format."""
        task_data = "{'d': {'area_id': [], 'exe': True, 'o': 100, 'region_id': [1], 'status': True, 'time': 2323}, 't': 'TASK'}"
        
        result = self.handler.parse_value(task_data)
        
        assert result is True
        assert self.handler.task_type == TaskType.TASK
        assert self.handler.area_id == []
        assert self.handler.execution_active is True
        assert self.handler.coverage_target == 100
        assert self.handler.region_id == [1]
        assert self.handler.task_active is True
        assert self.handler.elapsed_time == 2323

    def test_parse_task_dict_format(self):
        """Test parsing task descriptor from dict format."""
        task_data = {
            'd': {'area_id': [2, 3], 'exe': False, 'o': 80, 'region_id': [2, 3], 'status': False, 'time': 1800}, 
            't': 'TASK'
        }
        
        result = self.handler.parse_value(task_data)
        
        assert result is True
        assert self.handler.task_type == TaskType.TASK
        assert self.handler.area_id == [2, 3]
        assert self.handler.execution_active is False
        assert self.handler.coverage_target == 80
        assert self.handler.region_id == [2, 3]
        assert self.handler.task_active is False
        assert self.handler.elapsed_time == 1800

    def test_parse_task_unknown_type(self):
        """Test parsing task with unknown type."""
        task_data = "{'d': {'area_id': [], 'exe': True, 'o': 100, 'region_id': [1], 'status': True, 'time': 2323}, 't': 'UNKNOWN'}"
        
        result = self.handler.parse_value(task_data)
        
        assert result is True
        assert self.handler.task_type == TaskType.UNKNOWN

    def test_parse_task_invalid_format(self):
        """Test parsing invalid task format."""
        result = self.handler.parse_value("invalid json")
        assert result is False
        
        result = self.handler.parse_value(123)
        assert result is False

    def test_parse_task_paused_docked_state(self):
        """Test parsing task descriptor for paused/docked state (minimal fields)."""
        # This is the real-world case from the error log
        task_data = {'d': {'exe': True, 'o': 4, 'status': True}, 't': 'TASK'}
        
        result = self.handler.parse_value(task_data)
        
        assert result is True
        assert self.handler.task_type == TaskType.TASK
        assert self.handler.execution_active is True
        assert self.handler.coverage_target == 4
        assert self.handler.task_active is True
        # Optional fields should have default values
        assert self.handler.area_id is None
        assert self.handler.region_id is None
        assert self.handler.elapsed_time is None

    def test_get_notification_data(self):
        """Test getting notification data."""
        task_data = "{'d': {'area_id': [1, 2], 'exe': True, 'o': 75, 'region_id': [1], 'status': True, 'time': 1500}, 't': 'TASK'}"
        self.handler.parse_value(task_data)
        
        notification = self.handler.get_notification_data()
        
        expected = {
            'type': 'TASK',
            'area_id': [1, 2],
            'execution_active': True,
            'coverage_target': 75,
            'region_id': [1],
            'task_active': True,
            'elapsed_time': 1500,
        }
        assert notification == expected


class TestDndTimeHandler:
    """Test DndTimeHandler for property 2:51."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = DndTimeHandler()

    def test_parse_dnd_schedule_string_literal(self):
        """Test parsing DND schedule from string literal format."""
        dnd_data = "{'end': 858, 'start': 855, 'value': 1}"
        
        result = self.handler.parse_value(dnd_data)
        
        assert result is True
        assert self.handler.payload_type == Property51Type.DND_SCHEDULE
        assert self.handler.dnd_start_minute == 855
        assert self.handler.dnd_end_minute == 858
        assert self.handler.dnd_enabled is True

    def test_parse_dnd_schedule_dict_format(self):
        """Test parsing DND schedule from dict format."""
        dnd_data = {'end': 900, 'start': 600, 'value': 0}
        
        result = self.handler.parse_value(dnd_data)
        
        assert result is True
        assert self.handler.payload_type == Property51Type.DND_SCHEDULE
        assert self.handler.dnd_start_minute == 600
        assert self.handler.dnd_end_minute == 900
        assert self.handler.dnd_enabled is False

    def test_parse_time_sync_string_literal(self):
        """Test parsing time sync from string literal format."""
        time_data = "{'time': '1757011214', 'tz': 'Europe/Rome'}"
        
        result = self.handler.parse_value(time_data)
        
        assert result is True
        assert self.handler.payload_type == Property51Type.TIME_SYNC
        assert self.handler.sync_timestamp == '1757011214'
        assert self.handler.sync_timezone == 'Europe/Rome'

    def test_parse_time_sync_dict_format(self):
        """Test parsing time sync from dict format."""
        time_data = {'time': '1758748364', 'tz': 'Europe/Berlin'}
        
        result = self.handler.parse_value(time_data)
        
        assert result is True
        assert self.handler.payload_type == Property51Type.TIME_SYNC
        assert self.handler.sync_timestamp == '1758748364'
        assert self.handler.sync_timezone == 'Europe/Berlin'

    def test_parse_dnd_sequence(self):
        """Test parsing sequence of DND changes from real-world data."""
        # Enable: start 795 (13:15), end 798 (13:18), value 1
        result = self.handler.parse_value("{'end': 798, 'start': 795, 'value': 1}")
        assert result is True
        assert self.handler.dnd_enabled is True
        assert self.handler.dnd_start_minute == 795
        assert self.handler.dnd_end_minute == 798
        
        # Disable: same window, value 0
        result = self.handler.parse_value("{'end': 798, 'start': 795, 'value': 0}")
        assert result is True
        assert self.handler.dnd_enabled is False
        assert self.handler.dnd_start_minute == 795
        assert self.handler.dnd_end_minute == 798
        
        # Adjust end: end 858 (14:18), value 0
        result = self.handler.parse_value("{'end': 858, 'start': 795, 'value': 0}")
        assert result is True
        assert self.handler.dnd_enabled is False
        assert self.handler.dnd_start_minute == 795
        assert self.handler.dnd_end_minute == 858
        
        # Adjust start: start 855 (14:15), value 0
        result = self.handler.parse_value("{'end': 858, 'start': 855, 'value': 0}")
        assert result is True
        assert self.handler.dnd_enabled is False
        assert self.handler.dnd_start_minute == 855
        assert self.handler.dnd_end_minute == 858

    def test_parse_unknown_format(self):
        """Test parsing unknown format."""
        result = self.handler.parse_value("{'unknown': 'format'}")
        assert result is False
        assert self.handler.payload_type == Property51Type.UNKNOWN

    def test_get_dnd_notification_data(self):
        """Test getting DND notification data."""
        self.handler.parse_value("{'end': 900, 'start': 600, 'value': 1}")
        
        notification = self.handler.get_dnd_notification_data()
        
        expected = {
            'start_minute': 600,
            'end_minute': 900,
            'enabled': True,
        }
        assert notification == expected

    def test_get_time_sync_notification_data(self):
        """Test getting time sync notification data."""
        self.handler.parse_value("{'time': '1757011214', 'tz': 'Europe/Rome'}")
        
        notification = self.handler.get_time_sync_notification_data()
        
        expected = {
            'timestamp': '1757011214',
            'timezone': 'Europe/Rome',
        }
        assert notification == expected

    def test_parse_charging_schedule_format(self):
        """Test parsing charging schedule format."""
        charging_data = {'value': [15, 95, 0, 0, 1080, 480]}
        
        result = self.handler.parse_value(charging_data)
        
        # DndTimeHandler now handles charging schedule format
        assert result is True
        assert self.handler.payload_type == Property51Type.CHARGING_SCHEDULE
        
        # Check that charging handler was populated
        charging_handler = self.handler.charging_handler
        assert charging_handler.auto_recharge_percent == 15
        assert charging_handler.resume_percent == 95
        assert charging_handler.enabled is False  # 4th element is 0
        assert charging_handler.start_minute == 1080  # 18:00
        assert charging_handler.end_minute == 480     # 08:00

    def test_parse_third_variant_format(self):
        """Test parsing third variant format."""
        third_variant_data = {'value': [3198, 9591, 0]}
        
        result = self.handler.parse_value(third_variant_data)
        
        # DndTimeHandler now handles third variant format
        assert result is True
        assert self.handler.payload_type == Property51Type.THIRD_VARIANT
        
        # Check that third variant handler was populated
        third_variant_handler = self.handler.third_variant_handler
        assert third_variant_handler.value1 == 3198
        assert third_variant_handler.value2 == 9591
        assert third_variant_handler.value3 == 0

    def test_parse_fourth_variant_format(self):
        """Test parsing fourth variant format (single integer value)."""
        fourth_variant_data = {'value': 0}
        
        result = self.handler.parse_value(fourth_variant_data)
        
        # DndTimeHandler now handles fourth variant format
        assert result is True
        assert self.handler.payload_type == Property51Type.FOURTH_VARIANT
        
        # Check that fourth variant handler was populated
        fourth_variant_handler = self.handler.fourth_variant_handler
        assert fourth_variant_handler.value == 0

    def test_parse_fourth_variant_format_nonzero(self):
        """Test parsing fourth variant format with non-zero value."""
        fourth_variant_data = {'value': 42}
        
        result = self.handler.parse_value(fourth_variant_data)
        
        assert result is True
        assert self.handler.payload_type == Property51Type.FOURTH_VARIANT
        
        fourth_variant_handler = self.handler.fourth_variant_handler
        assert fourth_variant_handler.value == 42

    def test_parse_fifth_variant_format(self):
        """Test parsing fifth variant format (4-element array)."""
        fifth_variant_data = {'value': [1, 1, 0, 0]}
        
        result = self.handler.parse_value(fifth_variant_data)
        
        # DndTimeHandler now handles fifth variant format
        assert result is True
        assert self.handler.payload_type == Property51Type.FIFTH_VARIANT
        
        # Check that fifth variant handler was populated
        fifth_variant_handler = self.handler.fifth_variant_handler
        assert fifth_variant_handler.value1 == 1
        assert fifth_variant_handler.value2 == 1
        assert fifth_variant_handler.value3 == 0
        assert fifth_variant_handler.value4 == 0

    def test_parse_sixth_variant_format(self):
        """Test parsing sixth variant format ({'type': integer})."""
        sixth_variant_data = {'type': 1}
        
        result = self.handler.parse_value(sixth_variant_data)
        
        # DndTimeHandler now handles sixth variant format
        assert result is True
        assert self.handler.payload_type == Property51Type.SIXTH_VARIANT
        
        # Check that sixth variant handler was populated
        sixth_variant_handler = self.handler.sixth_variant_handler
        assert sixth_variant_handler.type_value == 1

    def test_parse_sixth_variant_format_zero(self):
        """Test parsing sixth variant format with zero value."""
        sixth_variant_data = {'type': 0}
        
        result = self.handler.parse_value(sixth_variant_data)
        
        assert result is True
        assert self.handler.payload_type == Property51Type.SIXTH_VARIANT
        
        sixth_variant_handler = self.handler.sixth_variant_handler
        assert sixth_variant_handler.type_value == 0

    def test_parse_multiple_variants_sequentially(self):
        """Test parsing different variants of property 2:51 sequentially."""
        # Start with DND schedule
        dnd_result = self.handler.parse_value("{'end': 900, 'start': 600, 'value': 1}")
        assert dnd_result is True
        assert self.handler.payload_type == Property51Type.DND_SCHEDULE
        assert self.handler.dnd_enabled is True
        
        # Parse time sync
        time_result = self.handler.parse_value("{'time': '1757011214', 'tz': 'Europe/Rome'}")
        assert time_result is True
        assert self.handler.payload_type == Property51Type.TIME_SYNC
        assert self.handler.sync_timezone == 'Europe/Rome'
        
        # Parse charging schedule
        charging_result = self.handler.parse_value({'value': [15, 95, 0, 0, 1080, 480]})
        assert charging_result is True
        assert self.handler.payload_type == Property51Type.CHARGING_SCHEDULE
        assert self.handler.charging_handler.auto_recharge_percent == 15
        
        # Parse third variant
        third_result = self.handler.parse_value({'value': [3198, 9591, 0]})
        assert third_result is True
        assert self.handler.payload_type == Property51Type.THIRD_VARIANT
        assert self.handler.third_variant_handler.value1 == 3198
        
        # Parse fourth variant
        fourth_result = self.handler.parse_value({'value': 0})
        assert fourth_result is True
        assert self.handler.payload_type == Property51Type.FOURTH_VARIANT
        assert self.handler.fourth_variant_handler.value == 0
        
        # Parse fifth variant
        fifth_result = self.handler.parse_value({'value': [1, 1, 0, 0]})
        assert fifth_result is True
        assert self.handler.payload_type == Property51Type.FIFTH_VARIANT
        assert self.handler.fifth_variant_handler.value1 == 1

    def test_notification_data_wrong_type(self):
        """Test getting notification data for wrong payload type."""
        # Parse DND but ask for time sync data
        self.handler.parse_value("{'end': 900, 'start': 600, 'value': 1}")
        assert self.handler.get_time_sync_notification_data() is None
        assert self.handler.get_charging_notification_data() is None
        assert self.handler.get_third_variant_notification_data() is None
        assert self.handler.get_fourth_variant_notification_data() is None
        assert self.handler.get_fifth_variant_notification_data() is None
        
        # Parse time sync but ask for DND data
        self.handler.parse_value("{'time': '1757011214', 'tz': 'Europe/Rome'}")
        assert self.handler.get_dnd_notification_data() is None
        assert self.handler.get_charging_notification_data() is None
        assert self.handler.get_third_variant_notification_data() is None
        assert self.handler.get_fourth_variant_notification_data() is None
        assert self.handler.get_fifth_variant_notification_data() is None
        
        # Parse charging but ask for others
        self.handler.parse_value({'value': [15, 95, 0, 0, 1080, 480]})
        assert self.handler.get_dnd_notification_data() is None
        assert self.handler.get_time_sync_notification_data() is None
        assert self.handler.get_third_variant_notification_data() is None
        assert self.handler.get_fourth_variant_notification_data() is None
        assert self.handler.get_fifth_variant_notification_data() is None
        
        # Parse third variant but ask for others
        self.handler.parse_value({'value': [3198, 9591, 0]})
        assert self.handler.get_dnd_notification_data() is None
        assert self.handler.get_time_sync_notification_data() is None
        assert self.handler.get_charging_notification_data() is None
        assert self.handler.get_fourth_variant_notification_data() is None
        assert self.handler.get_fifth_variant_notification_data() is None
        
        # Parse fourth variant but ask for others
        self.handler.parse_value({'value': 0})
        assert self.handler.get_dnd_notification_data() is None
        assert self.handler.get_time_sync_notification_data() is None
        assert self.handler.get_charging_notification_data() is None
        assert self.handler.get_third_variant_notification_data() is None
        assert self.handler.get_fifth_variant_notification_data() is None
        
        # Parse fifth variant but ask for others
        self.handler.parse_value({'value': [1, 1, 0, 0]})
        assert self.handler.get_dnd_notification_data() is None
        assert self.handler.get_time_sync_notification_data() is None
        assert self.handler.get_charging_notification_data() is None
        assert self.handler.get_third_variant_notification_data() is None
        assert self.handler.get_fourth_variant_notification_data() is None


class TestChargingHandler:
    """Test ChargingHandler for property 2:51 charging variant."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ChargingHandler()

    def test_parse_charging_schedule_dict_format(self):
        """Test parsing charging schedule from dict format."""
        charging_data = {'value': [15, 95, 0, 0, 1080, 480]}
        
        result = self.handler.parse_value(charging_data)
        
        assert result is True
        assert self.handler.auto_recharge_percent == 15
        assert self.handler.resume_percent == 95
        assert self.handler.enabled is False  # 4th element is 0
        assert self.handler.start_minute == 1080  # 18:00
        assert self.handler.end_minute == 480     # 08:00

    def test_parse_charging_schedule_enabled(self):
        """Test parsing charging schedule with enabled flag."""
        charging_data = {'value': [20, 80, 0, 1, 480, 1080]}
        
        result = self.handler.parse_value(charging_data)
        
        assert result is True
        assert self.handler.auto_recharge_percent == 20
        assert self.handler.resume_percent == 80
        assert self.handler.enabled is True  # 4th element is 1
        assert self.handler.start_minute == 480   # 08:00
        assert self.handler.end_minute == 1080    # 18:00

    def test_parse_invalid_format(self):
        """Test parsing invalid charging format."""
        # Missing 'value' key
        result = self.handler.parse_value({'invalid': 'format'})
        assert result is False
        
        # Wrong array length
        result = self.handler.parse_value({'value': [15, 95, 0]})
        assert result is False
        
        # Not a dict
        result = self.handler.parse_value("not a dict")
        assert result is False

    def test_get_notification_data(self):
        """Test getting notification data."""
        charging_data = {'value': [25, 90, 0, 1, 360, 1200]}
        self.handler.parse_value(charging_data)
        
        notification = self.handler.get_notification_data()
        
        expected = {
            'auto_recharge_percent': 25,
            'resume_percent': 90,
            'enabled': True,
            'start_minute': 360,
            'end_minute': 1200,
        }
        assert notification == expected


class TestThirdVariantHandler:
    """Test ThirdVariantHandler for property 2:51 third variant."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ThirdVariantHandler()

    def test_parse_third_variant_dict_format(self):
        """Test parsing third variant from dict format."""
        third_variant_data = {'value': [3198, 9591, 0]}
        
        result = self.handler.parse_value(third_variant_data)
        
        assert result is True
        assert self.handler.value1 == 3198
        assert self.handler.value2 == 9591
        assert self.handler.value3 == 0

    def test_parse_third_variant_from_issue(self):
        """Test parsing third variant with exact values from issue report.
        
        This test covers the specific message format reported in the issue:
        {'id': 767, 'method': 'properties_changed', 
         'params': [{'did': '-1******27', 'piid': 51, 'siid': 2, 
                     'value': {'value': [3198, 9591, 0]}}]}
        """
        # The 'value' part of the MQTT message
        third_variant_data = {'value': [3198, 9591, 0]}
        
        result = self.handler.parse_value(third_variant_data)
        
        assert result is True
        assert self.handler.value1 == 3198
        assert self.handler.value2 == 9591
        assert self.handler.value3 == 0
        
        # Verify notification data format
        notification = self.handler.get_notification_data()
        assert notification == {
            'value1': 3198,
            'value2': 9591,
            'value3': 0,
        }


    def test_parse_different_values(self):
        """Test parsing third variant with different values."""
        third_variant_data = {'value': [1234, 5678, 1]}
        
        result = self.handler.parse_value(third_variant_data)
        
        assert result is True
        assert self.handler.value1 == 1234
        assert self.handler.value2 == 5678
        assert self.handler.value3 == 1

    def test_parse_invalid_format(self):
        """Test parsing invalid third variant format."""
        # Missing 'value' key
        result = self.handler.parse_value({'invalid': 'format'})
        assert result is False
        
        # Wrong array length
        result = self.handler.parse_value({'value': [3198, 9591]})
        assert result is False
        
        # Not a dict
        result = self.handler.parse_value("not a dict")
        assert result is False

    def test_get_notification_data(self):
        """Test getting notification data."""
        third_variant_data = {'value': [1111, 2222, 3]}
        self.handler.parse_value(third_variant_data)
        
        notification = self.handler.get_notification_data()
        
        expected = {
            'value1': 1111,
            'value2': 2222,
            'value3': 3,
        }
        assert notification == expected


class TestFourthVariantHandler:
    """Test FourthVariantHandler for property 2:51 fourth variant."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = FourthVariantHandler()

    def test_parse_fourth_variant_dict_format_zero(self):
        """Test parsing fourth variant from dict format with zero value."""
        fourth_variant_data = {'value': 0}
        
        result = self.handler.parse_value(fourth_variant_data)
        
        assert result is True
        assert self.handler.value == 0

    def test_parse_fourth_variant_from_issue(self):
        """Test parsing fourth variant with exact values from issue report.
        
        This test covers the specific message format reported in the issue:
        {'id': 108, 'method': 'properties_changed', 
         'params': [{'did': '-1******27', 'piid': 51, 'siid': 2, 
                     'value': {'value': 0}}]}
        """
        # The 'value' part of the MQTT message
        fourth_variant_data = {'value': 0}
        
        result = self.handler.parse_value(fourth_variant_data)
        
        assert result is True
        assert self.handler.value == 0
        
        # Verify notification data format
        notification = self.handler.get_notification_data()
        assert notification == {'value': 0}

    def test_parse_fourth_variant_nonzero_value(self):
        """Test parsing fourth variant with non-zero values."""
        fourth_variant_data = {'value': 42}
        
        result = self.handler.parse_value(fourth_variant_data)
        
        assert result is True
        assert self.handler.value == 42
        
        # Test with negative value
        fourth_variant_data = {'value': -5}
        result = self.handler.parse_value(fourth_variant_data)
        
        assert result is True
        assert self.handler.value == -5

    def test_parse_invalid_format(self):
        """Test parsing invalid fourth variant format."""
        # Missing 'value' key
        result = self.handler.parse_value({'invalid': 'format'})
        assert result is False
        
        # Wrong value type (not integer)
        result = self.handler.parse_value({'value': 'not_an_int'})
        assert result is False
        
        # Wrong value type (list instead of int)
        result = self.handler.parse_value({'value': [0]})
        assert result is False
        
        # Not a dict
        result = self.handler.parse_value("not a dict")
        assert result is False

    def test_get_notification_data(self):
        """Test getting notification data."""
        fourth_variant_data = {'value': 123}
        self.handler.parse_value(fourth_variant_data)
        
        notification = self.handler.get_notification_data()
        
        expected = {'value': 123}
        assert notification == expected


class TestFifthVariantHandler:
    """Test FifthVariantHandler for property 2:51 fifth variant."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = FifthVariantHandler()

    def test_parse_fifth_variant_dict_format(self):
        """Test parsing fifth variant from dict format."""
        fifth_variant_data = {'value': [1, 1, 0, 0]}
        
        result = self.handler.parse_value(fifth_variant_data)
        
        assert result is True
        assert self.handler.value1 == 1
        assert self.handler.value2 == 1
        assert self.handler.value3 == 0
        assert self.handler.value4 == 0

    def test_parse_fifth_variant_from_issue(self):
        """Test parsing fifth variant with exact values from issue report.
        
        This test covers the specific message format reported in the issue:
        {'id': 131, 'method': 'properties_changed', 
         'params': [{'did': '-1******27', 'piid': 51, 'siid': 2, 
                     'value': {'value': [1, 1, 0, 0]}}]}
        """
        # The 'value' part of the MQTT message
        fifth_variant_data = {'value': [1, 1, 0, 0]}
        
        result = self.handler.parse_value(fifth_variant_data)
        
        assert result is True
        assert self.handler.value1 == 1
        assert self.handler.value2 == 1
        assert self.handler.value3 == 0
        assert self.handler.value4 == 0
        
        # Verify notification data format
        notification = self.handler.get_notification_data()
        assert notification == {
            'value1': 1,
            'value2': 1,
            'value3': 0,
            'value4': 0,
        }

    def test_parse_different_values(self):
        """Test parsing fifth variant with different values."""
        fifth_variant_data = {'value': [5, 10, 15, 20]}
        
        result = self.handler.parse_value(fifth_variant_data)
        
        assert result is True
        assert self.handler.value1 == 5
        assert self.handler.value2 == 10
        assert self.handler.value3 == 15
        assert self.handler.value4 == 20

    def test_parse_invalid_format(self):
        """Test parsing invalid fifth variant format."""
        # Missing 'value' key
        result = self.handler.parse_value({'invalid': 'format'})
        assert result is False
        
        # Wrong array length (too short)
        result = self.handler.parse_value({'value': [1, 1, 0]})
        assert result is False
        
        # Wrong array length (too long)
        result = self.handler.parse_value({'value': [1, 1, 0, 0, 0]})
        assert result is False
        
        # Not a dict
        result = self.handler.parse_value("not a dict")
        assert result is False

    def test_get_notification_data(self):
        """Test getting notification data."""
        fifth_variant_data = {'value': [7, 8, 9, 10]}
        self.handler.parse_value(fifth_variant_data)
        
        notification = self.handler.get_notification_data()
        
        expected = {
            'value1': 7,
            'value2': 8,
            'value3': 9,
            'value4': 10,
        }
        assert notification == expected


class TestSummaryHandler:
    """Test SummaryHandler for property 2:52."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SummaryHandler()

    def test_parse_empty_summary(self):
        """Test parsing empty summary (current behavior)."""
        result = self.handler.parse_value({})
        
        assert result is True
        assert self.handler.is_empty is True
        assert self.handler.summary_data == {}

    def test_parse_future_summary_data(self):
        """Test parsing future summary data with content."""
        summary_data = {
            'area': 150.5,
            'covered_area': 148.2,
            'duration': 3600,
            'result': 'completed',
            'zones': [1, 2],
            'energy_used': 25.5
        }
        
        result = self.handler.parse_value(summary_data)
        
        assert result is True
        assert self.handler.is_empty is False
        assert self.handler.summary_data == summary_data

    def test_parse_invalid_format(self):
        """Test parsing invalid summary format."""
        result = self.handler.parse_value("not a dict")
        assert result is False

    def test_get_notification_data(self):
        """Test getting notification data."""
        summary_data = {'area': 100, 'duration': 1800}
        self.handler.parse_value(summary_data)
        
        notification = self.handler.get_notification_data()
        assert notification == summary_data


class TestSchedulingPropertyHandler:
    """Test unified SchedulingPropertyHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SchedulingPropertyHandler()
        self.notifications = []
        
        def mock_notify(property_name, value):
            self.notifications.append((property_name, value))
        
        self.notify_callback = mock_notify

    def test_handle_task_property_mqtt_message(self):
        """Test handling task property from MQTT message format."""
        # Real MQTT message: {'id': 1119, 'method': 'properties_changed', 'params': [{'did': '-1xxxxxxx5', 'piid': 50, 'siid': 2, 'value': {'d': {'exe': True, 'o': 4, 'status': True}, 't': 'TASK'}}]}
        task_value = "{'d': {'area_id': [], 'exe': True, 'o': 100, 'region_id': [1], 'status': True, 'time': 2323}, 't': 'TASK'}"
        
        result = self.handler.handle_property_update(2, 50, task_value, self.notify_callback)
        
        assert result is True
        assert len(self.notifications) == 1
        assert self.notifications[0][0] == SCHEDULING_TASK_PROPERTY.name
        task_data = self.notifications[0][1]
        assert task_data['type'] == 'TASK'
        assert task_data['execution_active'] is True
        assert task_data['coverage_target'] == 100

    def test_handle_dnd_property_mqtt_message(self):
        """Test handling DND property from MQTT message format."""
        # Real MQTT messages from controlled session sequence
        dnd_value = "{'end': 858, 'start': 855, 'value': 1}"
        
        result = self.handler.handle_property_update(2, 51, dnd_value, self.notify_callback)
        
        assert result is True
        # Should have 4 notifications: dnd_enabled, dnd_start_time, dnd_end_time, scheduling_dnd
        assert len(self.notifications) == 4
        
        # Check individual notifications
        notify_dict = {name: value for name, value in self.notifications}
        assert notify_dict['dnd_enabled'] is True
        assert notify_dict['dnd_start_time'] == 855
        assert notify_dict['dnd_end_time'] == 858
        assert notify_dict[SCHEDULING_DND_PROPERTY.name] == {
            'start_minute': 855,
            'end_minute': 858, 
            'enabled': True
        }
        
        # Check handler state
        assert self.handler.dnd_enabled is True
        assert self.handler.dnd_start_time == 855
        assert self.handler.dnd_end_time == 858

    def test_handle_time_sync_property_mqtt_message(self):
        """Test handling time sync property from MQTT message format."""
        time_value = "{'time': '1757011214', 'tz': 'Europe/Rome'}"
        
        result = self.handler.handle_property_update(2, 51, time_value, self.notify_callback)
        
        assert result is True
        # Should have 3 notifications: timezone, device_time, scheduling_time_sync
        assert len(self.notifications) == 3
        
        notify_dict = {name: value for name, value in self.notifications}
        assert notify_dict['timezone'] == 'Europe/Rome'
        assert notify_dict['device_time'] == '1757011214'
        assert notify_dict[SCHEDULING_TIME_SYNC_PROPERTY_NAME] == {
            'timestamp': '1757011214',
            'timezone': 'Europe/Rome'
        }
        
        # Check handler state
        assert self.handler.timezone == 'Europe/Rome'
        assert self.handler.device_time == '1757011214'

    def test_handle_charging_schedule_property_mqtt_message(self):
        """Test handling charging schedule property from MQTT message format."""
        # Real MQTT message: {'id': 181, 'method': 'properties_changed', 'params': [{'did': '-1******95', 'piid': 51, 'siid': 2, 'value': {'value': [15, 95, 0, 0, 1080, 480]}}]}
        charging_value = {'value': [15, 95, 0, 0, 1080, 480]}
        
        result = self.handler.handle_property_update(2, 51, charging_value, self.notify_callback)
        
        assert result is True
        # Should have notifications for charging schedule
        assert len(self.notifications) > 0
        
        # Check that we got charging schedule notifications
        notification_names = [name for name, _ in self.notifications]
        assert SCHEDULING_CHARGING_PROPERTY_NAME in notification_names
        
        # Find the charging notification
        charging_notification = None
        for name, value in self.notifications:
            if name == SCHEDULING_CHARGING_PROPERTY_NAME:
                charging_notification = value
                break
        
        assert charging_notification is not None
        assert charging_notification['auto_recharge_percent'] == 15
        assert charging_notification['resume_percent'] == 95
        assert charging_notification['enabled'] is False  # 4th element is 0
        assert charging_notification['start_minute'] == 1080  # 18:00
        assert charging_notification['end_minute'] == 480     # 08:00

    def test_handle_third_variant_property_mqtt_message(self):
        """Test handling third variant property from MQTT message format."""
        # Third variant: {'value': [3198, 9591, 0]}
        third_variant_value = {'value': [3198, 9591, 0]}
        
        result = self.handler.handle_property_update(2, 51, third_variant_value, self.notify_callback)
        
        # For now, this should return True but be handled as a placeholder
        assert result is True
        # Should have notification for third variant
        assert len(self.notifications) > 0
        
        # Check that we got third variant notification
        notification_names = [name for name, _ in self.notifications]
        assert SCHEDULING_THIRD_VARIANT_PROPERTY_NAME in notification_names

    def test_handle_third_variant_from_issue_report(self):
        """Test handling the exact third variant message from the issue report.
        
        This test verifies end-to-end handling of the message format from the issue:
        {'id': 767, 'method': 'properties_changed', 
         'params': [{'did': '-1******27', 'piid': 51, 'siid': 2, 
                     'value': {'value': [3198, 9591, 0]}}]}
        """
        # The 'value' part of the MQTT message
        third_variant_value = {'value': [3198, 9591, 0]}
        
        result = self.handler.handle_property_update(2, 51, third_variant_value, self.notify_callback)
        
        assert result is True
        assert len(self.notifications) > 0
        
        # Find the third variant notification
        third_variant_notification = None
        for name, value in self.notifications:
            if name == SCHEDULING_THIRD_VARIANT_PROPERTY_NAME:
                third_variant_notification = value
                break
        
        assert third_variant_notification is not None
        assert third_variant_notification['value1'] == 3198
        assert third_variant_notification['value2'] == 9591
        assert third_variant_notification['value3'] == 0

    def test_handle_fourth_variant_property_mqtt_message(self):
        """Test handling fourth variant property from MQTT message format."""
        # Fourth variant: {'value': 0}
        fourth_variant_value = {'value': 0}
        
        result = self.handler.handle_property_update(2, 51, fourth_variant_value, self.notify_callback)
        
        # Should return True and be handled correctly
        assert result is True
        # Should have notification for fourth variant
        assert len(self.notifications) > 0
        
        # Check that we got fourth variant notification
        notification_names = [name for name, _ in self.notifications]
        assert SCHEDULING_FOURTH_VARIANT_PROPERTY_NAME in notification_names
        
        # Find the fourth variant notification
        fourth_variant_notification = None
        for name, value in self.notifications:
            if name == SCHEDULING_FOURTH_VARIANT_PROPERTY_NAME:
                fourth_variant_notification = value
                break
        
        assert fourth_variant_notification is not None
        assert fourth_variant_notification['value'] == 0

    def test_handle_fourth_variant_from_issue_report(self):
        """Test handling the exact fourth variant message from the issue report.
        
        This test verifies end-to-end handling of the message format from the issue:
        {'id': 108, 'method': 'properties_changed', 
         'params': [{'did': '-1******27', 'piid': 51, 'siid': 2, 
                     'value': {'value': 0}}]}
        """
        # The 'value' part of the MQTT message
        fourth_variant_value = {'value': 0}
        
        result = self.handler.handle_property_update(2, 51, fourth_variant_value, self.notify_callback)
        
        assert result is True
        assert len(self.notifications) > 0
        
        # Find the fourth variant notification
        fourth_variant_notification = None
        for name, value in self.notifications:
            if name == SCHEDULING_FOURTH_VARIANT_PROPERTY_NAME:
                fourth_variant_notification = value
                break
        
        assert fourth_variant_notification is not None
        assert fourth_variant_notification['value'] == 0

    def test_handle_fifth_variant_property_mqtt_message(self):
        """Test handling fifth variant property from MQTT message format."""
        # Fifth variant: {'value': [1, 1, 0, 0]}
        fifth_variant_value = {'value': [1, 1, 0, 0]}
        
        result = self.handler.handle_property_update(2, 51, fifth_variant_value, self.notify_callback)
        
        # Should return True and be handled correctly
        assert result is True
        # Should have notification for fifth variant
        assert len(self.notifications) > 0
        
        # Check that we got fifth variant notification
        notification_names = [name for name, _ in self.notifications]
        assert SCHEDULING_FIFTH_VARIANT_PROPERTY_NAME in notification_names
        
        # Find the fifth variant notification
        fifth_variant_notification = None
        for name, value in self.notifications:
            if name == SCHEDULING_FIFTH_VARIANT_PROPERTY_NAME:
                fifth_variant_notification = value
                break
        
        assert fifth_variant_notification is not None
        assert fifth_variant_notification['value1'] == 1
        assert fifth_variant_notification['value2'] == 1
        assert fifth_variant_notification['value3'] == 0
        assert fifth_variant_notification['value4'] == 0

    def test_handle_fifth_variant_from_issue_report(self):
        """Test handling the exact fifth variant message from the issue report.
        
        This test verifies end-to-end handling of the message format from the issue:
        {'id': 131, 'method': 'properties_changed', 
         'params': [{'did': '-1******27', 'piid': 51, 'siid': 2, 
                     'value': {'value': [1, 1, 0, 0]}}]}
        """
        # The 'value' part of the MQTT message
        fifth_variant_value = {'value': [1, 1, 0, 0]}
        
        result = self.handler.handle_property_update(2, 51, fifth_variant_value, self.notify_callback)
        
        assert result is True
        assert len(self.notifications) > 0
        
        # Find the fifth variant notification
        fifth_variant_notification = None
        for name, value in self.notifications:
            if name == SCHEDULING_FIFTH_VARIANT_PROPERTY_NAME:
                fifth_variant_notification = value
                break
        
        assert fifth_variant_notification is not None
        assert fifth_variant_notification['value1'] == 1
        assert fifth_variant_notification['value2'] == 1
        assert fifth_variant_notification['value3'] == 0
        assert fifth_variant_notification['value4'] == 0


    def test_handle_summary_property_mqtt_message(self):
        """Test handling summary property from MQTT message format."""
        # Real MQTT message: {'id': 1109, 'method': 'properties_changed', 'params': [{'did': '-1xxxxxxx5', 'piid': 52, 'siid': 2, 'value': {}}]}
        summary_value = {}
        
        result = self.handler.handle_property_update(2, 52, summary_value, self.notify_callback)
        
        assert result is True
        assert len(self.notifications) == 1
        assert self.notifications[0][0] == SCHEDULING_SUMMARY_PROPERTY.name
        assert self.notifications[0][1] == {}

    def test_handle_non_scheduling_property(self):
        """Test handling non-scheduling property returns False."""
        # Battery property (3:1)
        result = self.handler.handle_property_update(3, 1, 85, self.notify_callback)
        
        assert result is False
        assert len(self.notifications) == 0

    def test_state_management_across_updates(self):
        """Test state management across multiple property updates."""
        # Initial state should be None
        assert self.handler.dnd_enabled is None
        assert self.handler.timezone is None
        
        # Update DND
        self.handler.handle_property_update(2, 51, "{'end': 900, 'start': 600, 'value': 1}", self.notify_callback)
        assert self.handler.dnd_enabled is True
        assert self.handler.dnd_start_time == 600
        
        # Update time sync - should coexist with DND state (different schemas)
        self.handler.handle_property_update(2, 51, "{'time': '1757011214', 'tz': 'Europe/Rome'}", self.notify_callback)
        assert self.handler.timezone == 'Europe/Rome'
        # Note: In the implementation, time sync clears DND state since they share same handler
        assert self.handler.dnd_enabled is None  # DND state cleared by time sync
        
        # Update DND again
        self.handler.handle_property_update(2, 51, "{'end': 1200, 'start': 480, 'value': 0}", self.notify_callback)
        assert self.handler.dnd_enabled is False
        assert self.handler.dnd_start_time == 480
        assert self.handler.dnd_end_time == 1200
        # Note: In the implementation, DND clears time sync state since they share same handler  
        assert self.handler.timezone is None  # Time sync state cleared by DND

    def test_real_world_mqtt_sequence(self):
        """Test real-world MQTT message sequence from analysis data."""
        # From mowing_session_analysis_20250904_081133.json controlled session sequence
        mqtt_sequence = [
            # Enable: start 795 (13:15), end 798 (13:18), value 1
            (2, 51, "{'end': 798, 'start': 795, 'value': 1}"),
            # Disable: same window, value 0  
            (2, 51, "{'end': 798, 'start': 795, 'value': 0}"),
            # Adjust end: end 858 (14:18), value 0
            (2, 51, "{'end': 858, 'start': 795, 'value': 0}"),
            # Adjust start: start 855 (14:15), value 0
            (2, 51, "{'end': 858, 'start': 855, 'value': 0}"),
        ]
        
        expected_states = [
            # After enable
            {'enabled': True, 'start': 795, 'end': 798},
            # After disable 
            {'enabled': False, 'start': 795, 'end': 798},
            # After adjust end
            {'enabled': False, 'start': 795, 'end': 858},
            # After adjust start
            {'enabled': False, 'start': 855, 'end': 858},
        ]
        
        for i, (siid, piid, value) in enumerate(mqtt_sequence):
            self.notifications.clear()
            result = self.handler.handle_property_update(siid, piid, value, self.notify_callback)
            
            assert result is True, f"Failed to parse message {i}: {value}"
            
            expected = expected_states[i]
            assert self.handler.dnd_enabled == expected['enabled'], f"Step {i}: DND enabled mismatch"
            assert self.handler.dnd_start_time == expected['start'], f"Step {i}: DND start time mismatch"
            assert self.handler.dnd_end_time == expected['end'], f"Step {i}: DND end time mismatch"

    def test_error_handling(self):
        """Test error handling for invalid data."""
        # Invalid task data
        result = self.handler.handle_property_update(2, 50, "invalid json", self.notify_callback)
        assert result is False
        
        # Invalid DND data
        result = self.handler.handle_property_update(2, 51, "{'incomplete': 'data'}", self.notify_callback)
        assert result is False
        
        # Invalid summary data
        result = self.handler.handle_property_update(2, 52, "not a dict", self.notify_callback)
        assert result is False

    def test_backward_compatibility_notifications(self):
        """Test that backward compatibility notifications are sent."""
        # DND update should send both new structured notifications and old compatibility ones
        self.handler.handle_property_update(2, 51, "{'end': 900, 'start': 600, 'value': 1}", self.notify_callback)
        
        notification_names = [name for name, _ in self.notifications]
        
        # Should include backward compatibility notifications
        assert 'dnd_enabled' in notification_names
        assert 'dnd_start_time' in notification_names  
        assert 'dnd_end_time' in notification_names
        
        # Should include new structured notification
        assert SCHEDULING_DND_PROPERTY.name in notification_names
        
        # Time sync should also have backward compatibility
        self.notifications.clear()
        self.handler.handle_property_update(2, 51, "{'time': '1757011214', 'tz': 'Europe/Rome'}", self.notify_callback)
        
        notification_names = [name for name, _ in self.notifications]
        assert 'timezone' in notification_names
        assert 'device_time' in notification_names
        assert SCHEDULING_TIME_SYNC_PROPERTY_NAME in notification_names

    def test_handle_property_2_51_sixth_variant(self):
        """Test handling sixth variant format (issue #135)."""
        # Test the real-world message from issue #135
        result = self.handler.handle_property_update(2, 51, {'type': 1}, self.notify_callback)
        
        assert result is True
        assert len(self.notifications) > 0
        
        # Should receive sixth variant notification
        notify_dict = {name: value for name, value in self.notifications}
        from custom_components.dreame_mower.dreame.property.scheduling import SCHEDULING_SIXTH_VARIANT_PROPERTY_NAME
        
        assert SCHEDULING_SIXTH_VARIANT_PROPERTY_NAME in notify_dict
        
        sixth_variant_data = notify_dict[SCHEDULING_SIXTH_VARIANT_PROPERTY_NAME]
        assert sixth_variant_data['type'] == 1
        
        # State should be cleared
        assert self.handler.dnd_enabled is None
        assert self.handler.dnd_start_time is None
        assert self.handler.dnd_end_time is None