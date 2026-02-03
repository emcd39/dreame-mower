#!/usr/bin/env python3
"""Get device writable properties using DreameMowerCloudBase class."""

import sys
import importlib.util
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_cloud_base():
    """Load DreameMowerCloudBase class."""
    # Load cloud_base module
    spec = importlib.util.spec_from_file_location(
        "cloud_base",
        project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
    )
    cloud_base = importlib.util.module_from_spec(spec)
    sys.modules["cloud_base"] = cloud_base
    spec.loader.exec_module(cloud_base)
    return cloud_base


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    cloud_base = load_cloud_base()

    print(f"\n[*] Connecting to Dreame cloud ({args.account_type}, {args.country})...")
    print(f"    Username: {args.username}")
    print(f"    Device ID: {args.device_id}")
    print()

    # Create cloud client
    cloud = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    print("[*] Attempting to connect...")
    if not cloud.connect():
        print("\n[!] Failed to connect")
        print("    Possible issues:")
        print("    1. Wrong username or password")
        print("    2. Wrong country code (try cn, eu, us, ru, sg)")
        print("    3. Wrong account type (try dreame or mova)")
        print()
        print("    Tips:")
        print("    - Dreamehome accounts usually use email")
        print("    - MOVAhome accounts use email or phone")
        print("    - China accounts use country='cn'")
        return 1

    print("[+] Connected!\n")

    # Get devices
    print("[*] Getting device list...")
    devices = cloud.get_devices()

    if not devices or "page" not in devices:
        print("[!] Failed to get devices")
        return 1

    # Find target device
    target_device = None
    records = devices["page"].get("records", [])
    for device in records:
        if device.get("did") == args.device_id:
            target_device = device
            break

    if not target_device:
        print(f"[!] Device {args.device_id} not found")
        print(f"\n[*] Available devices:")
        for device in records:
            print(f"  - {device.get('customName')} ({device.get('model')})")
            print(f"    ID: {device.get('did')}")
        return 1

    print(f"[+] Found device: {target_device.get('customName')}")
    print(f"    Model: {target_device.get('model')}")
    print()

    # Show available cloud_base methods
    print("="*60)
    print("AVAILABLE CLOUD_BASE METHODS")
    print("="*60)
    print("\n[*] Public methods that might be useful:")
    useful_methods = [
        "get_devices",
        "execute_action",
        "get_device_info",
        "get_device_props",
        "set_device_property",
        "get_homeroom",
    ]

    for method in useful_methods:
        if hasattr(cloud, method):
            print(f"  ✓ {method}")

    print()

    # Try to get device methods/actions
    print("="*60)
    print("ATTEMPTING TO GET DEVICE METHODS/ACTIONS")
    print("="*60)

    # Check if there's a method to get device specs
    if hasattr(cloud, "get_devices"):
        # The get_devices response already contains device info
        # Let's see what we can get from it
        pass

    # Check if device has any method-related info
    # The iotKeyValue file you found earlier might have more clues
    print("\n[*] From your earlier discovery:")
    print("    File: dreame.hold.w2422_iotKeyValue_translate_20.json")
    print("    States include:")
    print("      - 5: Self-Cleaning (正在自清洁)")
    print("      - 6: Drying (正在烘干)")
    print("      - 26: Hot water self-cleaning (正在热水自清洁)")
    print("      - 27: Deep hot water self-cleaning (正在深度热水自清洁)")
    print()
    print("[*] Next step: Find out how to trigger these states")
    print("    1. Look for writable properties")
    print("    2. Look for actions (siid/aiid)")
    print("    3. Check Dreamehome app with mitmproxy")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
