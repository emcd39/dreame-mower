#!/usr/bin/env python3
"""Simple device status checker using get_devices approach."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import cloud modules (the working way)
import importlib.util

# Load cloud_base
spec_base = importlib.util.spec_from_file_location(
    "cloud_base_module",
    project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
)
cloud_base = importlib.util.module_from_spec(spec_base)
spec_base.loader.exec_module(cloud_base)


def main():
    # Configuration
    USERNAME = "13484216239"
    PASSWORD = "jy01867382"
    COUNTRY = "cn"
    DEVICE_ID = "-110294569"

    print("\n[*] Connecting to cloud...")

    # Create cloud client
    cloud = cloud_base.DreameMowerCloudBase(
        username=USERNAME,
        password=PASSWORD,
        country=COUNTRY,
        account_type="dreame",
    )

    # Connect
    if not cloud.connect():
        print("[!] Login failed")
        print("    Check username/password")
        return 1

    print("[+] Logged in")

    # Get devices
    devices = cloud.get_devices()
    if not devices or "page" not in devices:
        print("[!] Failed to get devices")
        return 1

    records = devices["page"].get("records", [])
    target = None
    for d in records:
        if d.get("did") == DEVICE_ID:
            target = d
            break

    if not target:
        print(f"[!] Device {DEVICE_ID} not found")
        return 1

    print(f"\n[+] Device: {target.get('customName', 'Unknown')}")
    print(f"    Model: {target.get('model')}")
    print(f"    Battery: {target.get('battery')}%")
    print(f"    Status: {target.get('latestStatus')}")
    print(f"    Online: {target.get('online')}")

    # Show device info JSON
    print("\n[*] Full device info:")
    print(json.dumps(target, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
