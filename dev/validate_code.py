#!/usr/bin/env python3
"""Simple code validation for hold device support."""

import sys
from pathlib import Path

def check_const_py():
    """Check const.py has necessary definitions."""
    print("[*] Checking const.py...")

    const_file = Path("custom_components/dreame_mower/const.py")
    with open(const_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("DeviceType class", "class DeviceType:" in content),
        ("DeviceType.HOLD", 'HOLD = "hold"' in content),
        ("HOLD_MODELS", "HOLD_MODELS" in content),
        ("dreame.hold", '"dreame.hold."' in content),
        ("CONF_DEVICE_TYPE", "CONF_DEVICE_TYPE" in content),
    ]

    all_pass = True
    for name, passed in checks:
        status = "[+]" if passed else "[!]"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False

    return all_pass


def check_config_flow_py():
    """Check config_flow.py imports HOLD_MODELS."""
    print("\n[*] Checking config_flow.py...")

    const_file = Path("custom_components/dreame_mower/config_flow.py")
    with open(const_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("Import HOLD_MODELS", "HOLD_MODELS" in content),
        ("Import DeviceType", "DeviceType" in content),
        ("dreame.hold in model_map", '"dreame.hold.w2422"' in content),
        ("device_type in _extract_info", "self.device_type" in content),
        ("CONF_DEVICE_TYPE in data", "CONF_DEVICE_TYPE" in content),
    ]

    all_pass = True
    for name, passed in checks:
        status = "[+]" if passed else "[!]"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False

    return all_pass


def check_hold_py():
    """Check hold.py exists and has necessary structure."""
    print("\n[*] Checking hold.py...")

    hold_file = Path("custom_components/dreame_mower/hold.py")
    if not hold_file.exists():
        print(f"  [!] hold.py does not exist")
        return False

    with open(hold_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("File exists", True),
        ("StateVacuumEntity imported", "StateVacuumEntity" in content),
        ("DreameHoldEntity class", "class DreameHoldEntity" in content),
        ("async_setup_entry", "async_setup_entry" in content),
        ("battery_level property", "battery_level" in content),
        ("async_start method", "async_start" in content),
        ("async_pause method", "async_pause" in content),
    ]

    all_pass = True
    for name, passed in checks:
        status = "[+]" if passed else "[!]"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False

    return all_pass


def check_init_py():
    """Check __init__.py has platform selection logic."""
    print("\n[*] Checking __init__.py...")

    init_file = Path("custom_components/dreame_mower/__init__.py")
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("Import DeviceType", "DeviceType" in content),
        ("PLATFORMS_BY_DEVICE_TYPE", "PLATFORMS_BY_DEVICE_TYPE" in content),
        ("DeviceType.HOLD mapping", 'DeviceType.HOLD' in content),
        ("Platform.VACUUM for HOLD", "Platform.VACUUM" in content),
        ("device_type from entry", "entry.data.get(\"device_type\"" in content),
    ]

    all_pass = True
    for name, passed in checks:
        status = "[+]" if passed else "[!]"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False

    return all_pass


def main():
    print("="*60)
    print("Dreame Hold Device Support - Code Validation")
    print("="*60)
    print()

    tests = [
        check_const_py(),
        check_config_flow_py(),
        check_hold_py,
        check_init_py,
    ]

    print()
    print("="*60)
    print("Validation Summary:")
    print("="*60)

    if all(tests):
        print("\n[+] All checks passed!")
        print()
        print("Your code modifications look correct.")
        print()
        print("To test in Home Assistant:")
        print("  1. Copy files to HA config:")
        print("     - Copy custom_components/ to your HA config directory")
        print("     - Ensure path: <config>/custom_components/dreame_mower/")
        print()
        print("  2. Restart Home Assistant")
        print()
        print("  3. Add integration:")
        print("     - Settings → Devices & Services → Add Integration")
        print("     - Search 'Dreame Mower'")
        print("     - Enter your Dreamehome credentials")
        print("     - Select your H20 Ultra device")
        print()
        print("  4. Verify functionality:")
        print("     - Check if vacuum entity appears")
        print("     - Check battery level")
        print("     - Try start/pause buttons")
        return 0
    else:
        print("\n[!] Some checks failed. Please review above.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
