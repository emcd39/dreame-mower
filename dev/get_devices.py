"""Standalone device lister that directly imports cloud_base."""

import argparse
import getpass
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import cloud_base directly (bypassing __init__.py)
import importlib.util

# Load cloud_base module
spec = importlib.util.spec_from_file_location(
    "cloud_base",
    project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
)
cloud_base = importlib.util.module_from_spec(spec)
sys.modules["cloud_base"] = cloud_base

# Execute the module (this defines DreameMowerCloudBase)
spec.loader.exec_module(cloud_base)


def main():
    parser = argparse.ArgumentParser(description="List Dreame devices")
    parser.add_argument("--username", help="Cloud username (email)")
    parser.add_argument("--password", help="Cloud password")
    parser.add_argument("--country", help="Cloud country code (cn, eu, us, ru, sg)")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    args = parser.parse_args()

    # Get credentials
    if not args.username:
        args.username = input("Enter username (email): ")
    if not args.password:
        args.password = getpass.getpass("Enter password: ")
    if not args.country:
        country = input("Enter country code (cn, eu, us, ru, sg) [default: cn]: ").strip()
        args.country = country if country else "cn"

    print(f"\n🔌 Connecting to {args.account_type} cloud ({args.country})...\n")

    # Create cloud client using the imported class
    cloud = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    if not cloud.connect():
        print("❌ Failed to connect")
        print("Check your credentials and country code")
        print(f"\nTip: For Chinese accounts, use country='cn'")
        print(f"     For EU/US accounts, use country='eu' or 'us'")
        return 1

    print("✅ Connected!\n")

    # Get devices
    devices = cloud.get_devices()
    if not devices or "page" not in devices:
        print("❌ Failed to get devices")
        return 1

    records = devices["page"].get("records", [])
    if not records:
        print("No devices found")
        return 0

    print("=" * 70)
    print(f"📱 Found {len(records)} device(s):")
    print("=" * 70)

    for i, device in enumerate(records, 1):
        model = device.get("model", "unknown")
        did = device.get("did", "unknown")
        mac = device.get("mac", "unknown")
        custom_name = device.get("customName", "")
        display_name = device.get("deviceInfo", {}).get("displayName", "")

        print(f"\nDevice {i}:")
        print(f"  Model:    {model}")
        print(f"  Name:     {custom_name or display_name}")
        print(f"  DeviceID: {did}")
        print(f"  MAC:      {mac}")

        # Determine device type
        if model.startswith("dreame.mower.") or model.startswith("mova.mower."):
            print(f"  Type:     🟢 Lawn Mower (already supported)")
        elif model.startswith("dreame.vacuum.") or model.startswith("mova.vacuum."):
            print(f"  Type:     🔵 Vacuum/Wet-Dry Cleaner")
        else:
            print(f"  Type:     ❓ Unknown")

    print("\n" + "=" * 70)
    print("Full JSON:")
    print("=" * 70)
    print(json.dumps(devices, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
