#!/usr/bin/env python3
"""Test Dreame cloud login using DreameMowerCloudBase."""

import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_cloud_base():
    """Load DreameMowerCloudBase class."""
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
    args = parser.parse_args()

    print(f"\n[*] Testing Dreame cloud connection")
    print(f"    Username: {args.username}")
    print(f"    Country: {args.country}")
    print(f"    Account Type: {args.account_type}")
    print()

    cloud_base = load_cloud_base()

    # Create cloud client
    cloud = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    print("[*] Attempting to connect...")
    if cloud.connect():
        print("[+] Connection successful!")
        print()

        # Get devices
        print("[*] Getting device list...")
        devices = cloud.get_devices()

        if devices and "page" in devices:
            records = devices["page"].get("records", [])
            print(f"\n[+] Found {len(records)} devices:\n")

            for device in records:
                print(f"Device: {device.get('customName', 'Unknown')}")
                print(f"  Model: {device.get('model')}")
                print(f"  ID: {device.get('did')}")
                print(f"  MAC: {device.get('mac')}")
                print(f"  Online: {device.get('online')}")
                print(f"  Battery: {device.get('battery')}%")
                print(f"  Status: {device.get('latestStatus')}")
                print()
        else:
            print("[!] Failed to get devices")
    else:
        print("\n[!] Connection failed")
        print("    Possible issues:")
        print("    1. Wrong username or password")
        print("    2. Wrong country code (try cn, eu, us, ru, sg)")
        print("    3. Wrong account type (try dreame or mova)")
        print()
        print("    Tips:")
        print("    - Dreamehome accounts usually use email")
        print("    - MOVAhome accounts can use phone or email")
        print("    - China accounts use country='cn'")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
