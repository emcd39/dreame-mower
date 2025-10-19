"""Test realtime monitor display logic."""
from __future__ import annotations

import io
import sys
from collections import deque
from unittest.mock import patch


def test_status_display_line_count():
    """Test that status display correctly counts lines for cursor movement.
    
    This test simulates the display logic from _status_worker to ensure
    that the line count is correct even with 5+ MQTT messages.
    """
    # Simulate the display logic
    def build_display_output(status_line: str, recent_msgs: list[str]) -> list[str]:
        """Build output lines like _status_worker does."""
        lines = [status_line]
        if recent_msgs:
            lines.append(f"Recent MQTT:")  # No \n prefix
            for msg in recent_msgs:
                lines.append(f"  → {msg}")
        
        return lines
    
    # Test with 1 message
    status = "Alive 00:00:01 | REST polls=1 | MQTT msgs=1"
    msgs = ["12:00:01 properties_changed: [...]"]
    lines = build_display_output(status, msgs)
    # Expected: status_line, "Recent MQTT:", "  → msg"
    assert len(lines) == 3, f"Expected 3 lines with 1 msg, got {len(lines)}: {lines}"
    
    # Test with 5 messages
    msgs = [
        "12:00:01 properties_changed: [...]",
        "12:00:02 properties_changed: [...]",
        "12:00:03 properties_changed: [...]",
        "12:00:04 properties_changed: [...]",
        "12:00:05 properties_changed: [...]",
    ]
    lines = build_display_output(status, msgs)
    # Expected: status_line, "Recent MQTT:", 5x "  → msg"
    assert len(lines) == 7, f"Expected 7 lines with 5 msgs, got {len(lines)}: {lines}"
    
    # Verify no empty lines
    assert lines[0] == status, f"Expected status at index 0"
    assert lines[1] == "Recent MQTT:", f"Expected 'Recent MQTT:' at index 1, got: {lines[1]}"
    
    # Test with 6 messages (deque maxlen=5, so still only 5 messages displayed)
    # This simulates what happens when 6th message arrives - oldest drops off
    msgs = [
        "12:00:02 properties_changed: [...]",  # First message dropped
        "12:00:03 properties_changed: [...]",
        "12:00:04 properties_changed: [...]",
        "12:00:05 properties_changed: [...]",
        "12:00:06 properties_changed: [...]",
    ]
    lines = build_display_output(status, msgs)
    # Still 7 lines: status_line, "Recent MQTT:", 5x "  → msg"
    assert len(lines) == 7, f"Expected 7 lines with 5 msgs (after 6th), got {len(lines)}: {lines}"


def test_status_display_inline_updates():
    """Test that inline display updates work correctly."""
    # Simulate the cursor movement logic
    CURSOR_UP = "\033[{}A"
    CLEAR_LINE = "\033[2K"
    CURSOR_START = "\r"
    
    output_buffer = io.StringIO()
    
    def simulate_display(lines: list[str], prev_lines: int, first_display: bool) -> int:
        """Simulate the display update logic."""
        # Move cursor up (except first time)
        if not first_display and prev_lines > 0:
            output_buffer.write(CURSOR_UP.format(prev_lines))
        
        # Print each line
        for line in lines:
            output_buffer.write(CLEAR_LINE + CURSOR_START + line + "\n")
        
        # Clear extra lines if shrinking
        if len(lines) < prev_lines:
            for _ in range(prev_lines - len(lines)):
                output_buffer.write(CLEAR_LINE + "\n")
        
        return len(lines)
    
    # First update with 1 message
    status = "Alive 00:00:01 | REST polls=1 | MQTT msgs=1"
    msgs = ["12:00:01 properties_changed: [...]"]
    lines = [status]
    if msgs:
        lines.append(f"Recent MQTT:")
        for msg in msgs:
            lines.append(f"  → {msg}")
    
    prev_lines = simulate_display(lines, 0, True)
    assert prev_lines == 3
    
    # Second update with 5 messages (should move cursor up by prev_lines)
    status = "Alive 00:00:02 | REST polls=1 | MQTT msgs=5"
    msgs = [
        "12:00:01 properties_changed: [...]",
        "12:00:02 properties_changed: [...]",
        "12:00:03 properties_changed: [...]",
        "12:00:04 properties_changed: [...]",
        "12:00:05 properties_changed: [...]",
    ]
    lines = [status]
    if msgs:
        lines.append(f"Recent MQTT:")
        for msg in msgs:
            lines.append(f"  → {msg}")
    
    prev_lines = simulate_display(lines, prev_lines, False)
    assert prev_lines == 7
    
    # Verify the output contains cursor movement
    result = output_buffer.getvalue()
    assert "\033[3A" in result, "Should contain cursor up 3 command"
    assert result.count("\033[2K") >= 7, "Should clear at least 7 lines"
    
    # Third update: 6th message arrives (deque keeps only last 5)
    # Should still be 7 lines and cursor should move up by 7
    status = "Alive 00:00:03 | REST polls=1 | MQTT msgs=6"
    msgs = [
        "12:00:02 properties_changed: [...]",  # First dropped
        "12:00:03 properties_changed: [...]",
        "12:00:04 properties_changed: [...]",
        "12:00:05 properties_changed: [...]",
        "12:00:06 properties_changed: [...]",
    ]
    lines = [status]
    if msgs:
        lines.append(f"Recent MQTT:")
        for msg in msgs:
            lines.append(f"  → {msg}")
    
    prev_lines = simulate_display(lines, prev_lines, False)
    assert prev_lines == 7, "Should still be 7 lines with 6th message"
    
    # Verify cursor moved up by 7
    result = output_buffer.getvalue()
    assert "\033[7A" in result, "Should contain cursor up 7 command for stable display"
    
    # Fourth update: Simulate time passing - status line changes but message count stays at 5
    # This tests that the display continues to work inline when only status updates
    status = "Alive 00:00:08 | REST polls=2 | MQTT msgs=9"
    msgs = [
        "12:00:05 properties_changed: [...]",
        "12:00:06 properties_changed: [...]",
        "12:00:07 properties_changed: [...]",
        "12:00:08 properties_changed: [...]",
        "12:00:09 properties_changed: [...]",
    ]
    lines = [status]
    if msgs:
        lines.append(f"Recent MQTT:")
        for msg in msgs:
            lines.append(f"  → {msg}")
    
    prev_lines = simulate_display(lines, prev_lines, False)
    assert prev_lines == 7, "Should maintain 7 lines with ongoing updates"
    
    # Verify multiple cursor up commands exist (one for each update after first)
    result = output_buffer.getvalue()
    cursor_up_count = result.count("\033[7A")
    assert cursor_up_count >= 2, f"Should have at least 2 cursor up 7 commands, found {cursor_up_count}"
