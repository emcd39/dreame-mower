#!/usr/bin/env python3
"""Query device properties using different siid values."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import importlib.util

# Load cloud_base module
spec = importlib.util.spec_from_file_location(
    "cloud_base",
    project_root / "custom_components" / "dreame_mower" / "dreame" / "cloud" / "cloud_base.py"
)
cloud_base = importlib.util.module_from_spec(spec)
sys.modules["cloud_base"] = cloud_base
spec.loader.exec_module(cloud_base)


def query_property(cloud, device_id, siid, piid):
    """Query a single property."""
    api = cloud._api_strings
    url = f"{cloud.get_api_url()}/{api[23]}/{api[26]}/{api[44]}"

    data = {
        "did": device_id,
        api[35]: [{"did": str(device_id), "siid": siid, "piid": piid}]
    }

    headers = {
        "Content-Type": "application/json",
        api[46]: cloud._key,
    }
    if cloud._country == "cn":
        headers[api[48]] = api[4]

    response = cloud._session.post(url, json=data, headers=headers, timeout=30)

    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            return {"error": result.get("msg", "Unknown error")}
    else:
        return {"error": f"HTTP {response.status_code}"}


def main():
    parser = argparse.ArgumentParser(description="Query device properties")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    # Create cloud client
    cloud = cloud_base.DreameMowerCloudBase(
        username=args.username,
        password=args.password,
        country=args.country,
        account_type=args.account_type,
    )

    # Connect
    print("[*] Connecting...")
    if not cloud.connect():
        print("[!] Failed to connect")
        return 1

    print("[+] Connected!\n")

    # Common siid values for Dreame devices
    # Based on MIoT spec, common services:
    # - siid 3: Device Information
    # - siid 4: Vacuum (mopping/cleaning)
    # - siid 5: Battery
    # - siid 6: Clean (mop washing)
    # - siid 7: Dry (mop drying)
    # - siid 8: Brush (maintenance)
    # - siid 16-18: Dock/Station functions (for robot vacuums)

    test_properties = [
        # Device info (siid 3)
        (3, 1, "Device Manufacturer"),
        (3, 2, "Device Model"),
        (3, 3, "Device Serial Number"),
        (3, 4, "Firmware Version"),

        # Vacuum/Mop (siid 4)
        (4, 1, "Status / State"),
        (4, 2, "Error Code"),
        (4, 3, "Cleaning Mode"),
        (4, 4, "Suction Level"),

        # Battery (siid 5)
        (5, 1, "Battery Level"),
        (5, 2, "Charging State"),

        # Clean/Wash (siid 6)
        (6, 1, "Wash Status"),
        (6, 2, "Wash Mode"),
        (6, 3, "Water Level"),

        # Dry (siid 7)
        (7, 1, "Drying Status"),
        (7, 2, "Drying Mode"),

        # Brush/Filter (siid 8)
        (8, 1, "Main Brush Life"),
        (8, 2, "Filter Life"),
        (8, 3, "Mop Life"),

        # Additional common properties
        (10, 1, "Clean Record"),
        (11, 1, "Dust Collection Count"),

        # Try higher siids for dock functions
        (16, 1, "Dock Wash Status"),
        (17, 1, "Dock Dry Status"),
    ]

    print("="*60)
    print("QUERYING DEVICE PROPERTIES")
    print("="*60 + "\n")

    found_properties = []

    for siid, piid, description in test_properties:
        print(f"[*] Querying [{siid}:{piid}] {description}...")

        result = query_property(cloud, args.device_id, siid, piid)

        if result and "error" not in result:
            # Success!
            print(f"    [+] Found: {result}")

            # Extract property name and value
            for key, value in result.items():
                found_properties.append({
                    "siid": siid,
                    "piid": piid,
                    "name": key,
                    "value": value,
                    "description": description
                })
        else:
            print(f"    [-] {result.get('error', 'No data')}")

        print()

    # Summary
    if found_properties:
        print("="*60)
        print("FOUND PROPERTIES")
        print("="*60 + "\n")

        for prop in found_properties:
            print(f"[{prop['siid']}:{prop['piid']}] {prop['name']}")
            print(f"  Description: {prop['description']}")
            print(f"  Value: {prop['value']}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
