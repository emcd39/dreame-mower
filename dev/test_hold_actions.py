#!/usr/bin/env python3
"""Test different siid/aiid combinations for hold device."""

import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_cloud_modules():
    """Load cloud modules bypassing __init__.py."""
    # Create synthetic module hierarchy
    sys.modules["dreame_mower"] = type(sys)("dreame_mower")
    sys.modules["dreame_mower.dreame"] = type(sys)("dreame_mower.dreame")
    sys.modules["dreame_mower.dreame.cloud"] = type(sys)("dreame_mower.dreame.cloud")

    # Load const first
    spec_const = importlib.util.spec_from_file_location(
        "dreame_mower.dreame.const",
        project_root / "custom_components" / "dreame_mower" / "dreame" / "const.py"
    )
    const_module = importlib.util.module_from_spec(spec_const)
    sys.modules["dreame_mower.dreame.const"] = const_module
    spec_const.loader.exec_module(const_module)

    # Load cloud_base
    spec_base = importlib.util.spec_from_file_location(
        "dreame_mower.dreame.cloud.cloud_base",
        project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
    )
    cloud_base = importlib.util.module_from_spec(spec_base)
    sys.modules["dreame_mower.dreame.cloud.cloud_base"] = cloud_base
    spec_base.loader.exec_module(cloud_base)

    return cloud_base


def test_action(device, siid, aiid, name):
    """Test a single action."""
    from custom_components.dreame_mower.dreame.const import ActionIdentifier

    action = ActionIdentifier(siid=siid, aiid=aiid, name=name)

    try:
        result = device.execute_action(action)
        if result:
            print(f"  ✓ SUCCESS: {name} (siid={siid}, aiid={aiid})")
            return True
        else:
            print(f"  ✗ FAILED: {name} (siid={siid}, aiid={aiid}) - No error but returned False")
            return False
    except Exception as ex:
        print(f"  ✗ ERROR: {name} (siid={siid}, aiid={aiid}) - {ex}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    # Load modules
    cloud_base = load_cloud_modules()

    print(f"\n[*] Connecting to Dreame cloud ({args.country})...")
    print(f"[+] Device ID: {args.device_id}\n")

    # Create auth and device
    auth = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type="dreame",
    )

    auth.connect()

    if not auth.connected:
        print("[!] Failed to connect")
        return 1

    print("[+] Connected\n")

    # Get cloud device
    from custom_components.dreame_mower.dreame.cloud.cloud_device import DreameMowerCloudDevice
    device = DreameMowerCloudDevice(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type="dreame",
        device_id=args.device_id,
    )

    # Test different siid/aiid combinations
    print("="*60)
    print("TESTING DIFFERENT SIID/AIID COMBINATIONS")
    print("="*60)

    # Common siid values for washers (3-20)
    test_combinations = [
        # Basic controls (should work with siid=5)
        (5, 1, "Start"),
        (5, 2, "Stop"),
        (5, 4, "Pause"),

        # Self-clean attempts (various siid)
        (6, 1, "Self Clean (siid=6)"),
        (8, 1, "Self Clean (siid=8)"),
        (10, 1, "Self Clean (siid=10)"),
        (12, 1, "Self Clean (siid=12)"),
        (13, 1, "Self Clean (siid=13)"),
        (14, 1, "Self Clean (siid=14)"),
        (15, 1, "Self Clean (siid=15)"),
        (16, 1, "Self Clean (siid=16)"),
        (18, 1, "Self Clean (siid=18)"),

        # Drying attempts
        (7, 1, "Drying (siid=7)"),
        (9, 1, "Drying (siid=9)"),
        (11, 1, "Drying (siid=11)"),
        (15, 1, "Drying (siid=15)"),
        (17, 1, "Drying (siid=17)"),
        (19, 1, "Drying (siid=19)"),
    ]

    successful = []
    for siid, aiid, name in test_combinations:
        if test_action(device, siid, aiid, name):
            successful.append((siid, aiid, name))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nTotal tested: {len(test_combinations)}")
    print(f"Successful: {len(successful)}")

    if successful:
        print("\n✓ Working combinations:")
        for siid, aiid, name in successful:
            print(f"  - {name}: siid={siid}, aiid={aiid}")

        print("\n📝 Update const.py with these values:")
        print("```python")
        for siid, aiid, name in successful:
            if "Self Clean" in name:
                print(f"HOLD_ACTION_START_SELF_CLEAN = ActionIdentifier(siid={siid}, aiid={aiid}, name=\"start_self_clean\")")
            elif "Drying" in name:
                print(f"HOLD_ACTION_START_DRYING = ActionIdentifier(siid={siid}, aiid={aiid}, name=\"start_drying\")")
        print("```")
    else:
        print("\n[!] No working combinations found.")
        print("[*] The device may not support these actions via MIoT API")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
