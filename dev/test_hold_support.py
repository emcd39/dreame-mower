#!/usr/bin/env python3
"""Test script to verify basic hold device support."""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all modules can be imported."""
    print("[*] Testing imports...")

    try:
        from custom_components.dreame_mower import const
        print(f"[+] const imported: DeviceType={const.DeviceType}")
        print(f"[+] HOLD_MODELS: {const.HOLD_MODELS}")
    except Exception as e:
        print(f"[!] Failed to import const: {e}")
        return False

    try:
        from custom_components.dreame_mower import hold
        print(f"[+] hold module imported")
    except Exception as e:
        print(f"[!] Failed to import hold: {e}")
        return False

    try:
        from custom_components.dreame_mower import config_flow
        print(f"[+] config_flow imported")
        print(f"[+] DREAME_MODELS includes hold: {any('hold' in m for m in config_flow.DREAME_MODELS)}")
    except Exception as e:
        print(f"[!] Failed to import config_flow: {e}")
        return False

    return True


def test_device_detection():
    """Test if hold device would be detected."""
    print("\n[*] Testing device detection...")

    # Simulate device info from API
    test_device = {
        "did": "-110294569",
        "model": "dreame.hold.w2422",
        "customName": "H20 Ultra 测试",
        "battery": 100,
        "latestStatus": 7,
    }

    # Check if model starts with any hold prefix
    from custom_components.dreame_mower.const import HOLD_MODELS

    is_hold = any(test_device["model"].startswith(prefix) for prefix in HOLD_MODELS)

    if is_hold:
        print(f"[+] Device '{test_device['model']}' correctly identified as HOLD device")
        print(f"[+] Device type would be: hold")
    else:
        print(f"[!] Device '{test_device['model']}' NOT identified as HOLD device")
        return False

    return True


def test_platform_selection():
    """Test if correct platform would be selected."""
    print("\n[*] Testing platform selection...")

    from custom_components.dreame_mower.const import DeviceType
    from custom_components.dreame_mower import __init__

    device_type = DeviceType.HOLD
    platforms = __init__.PLATFORMS_BY_DEVICE_TYPE.get(device_type)

    if platforms:
        print(f"[+] Platforms for HOLD device: {platforms}")
        print(f"[+] vacuum platform included: {__init__.Platform.VACUUM in platforms}")
    else:
        print(f"[!] No platforms found for HOLD device")
        return False

    return True


def main():
    print("="*60)
    print("Dreame Hold Device Support - Basic Functionality Test")
    print("="*60)
    print()

    tests = [
        ("Module Imports", test_imports),
        ("Device Detection", test_device_detection),
        ("Platform Selection", test_platform_selection),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n[!] Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # Summary
    print()
    print("="*60)
    print("Test Summary:")
    print("="*60)

    all_passed = True
    for name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("[+] All tests passed! Basic functionality looks good.")
        print()
        print("Next steps:")
        print("  1. Copy custom_components directory to your HA config")
        print("  2. Restart Home Assistant")
        print("  3. Add integration via UI")
        print("  4. Test device connection and controls")
    else:
        print("[!] Some tests failed. Please review the errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
