#!/usr/bin/env python3
"""Test device actions using different siid/aiid combinations."""

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


def execute_action(cloud, device_id, siid, aiid, params=None):
    """Execute a device action."""
    api = cloud._api_strings

    # Build the endpoint for action
    # Based on cloud_device.py send() method
    host = ""
    url = f"{cloud.get_api_url()}/{api[37]}{host}/{api[27]}/{api[38]}"

    data = {
        "did": str(device_id),
        "id": 1,  # Request ID
        "data": {
            "did": str(device_id),
            "id": 1,
            "method": "action",
            "params": {
                "did": str(device_id),
                "siid": siid,
                "aiid": aiid,
                "in": params or [],
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        api[46]: cloud._key,
    }
    if cloud._country == "cn":
        headers[api[48]] = api[4]

    response = cloud._session.post(url, json=data, headers=headers, timeout=30)

    return response


def main():
    parser = argparse.ArgumentParser(description="Test device actions")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--country", default="cn")
    parser.add_argument("--account-type", default="dreame", choices=["dreame", "mova"])
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Don't actually execute, just show what would be done")
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

    # Test actions to try
    # Based on common MIoT patterns for handheld wet/dry vacuums
    test_actions = [
        # Basic cleaning control
        {"siid": 5, "aiid": 1, "name": "Start Cleaning", "params": []},
        {"siid": 5, "aiid": 2, "name": "Stop Cleaning", "params": []},
        {"siid": 5, "aiid": 4, "name": "Pause Cleaning", "params": []},

        # Self-cleaning (most likely to work)
        {"siid": 6, "aiid": 1, "name": "Start Self-Clean", "params": []},
        {"siid": 6, "aiid": 2, "name": "Stop Self-Clean", "params": []},

        # Drying
        {"siid": 7, "aiid": 1, "name": "Start Drying", "params": []},
        {"siid": 7, "aiid": 2, "name": "Stop Drying", "params": []},

        # With mode parameters
        {"siid": 6, "aiid": 1, "name": "Start Self-Clean (Mode=Normal)", "params": [1]},
        {"siid": 6, "aiid": 1, "name": "Start Self-Clean (Mode=Hot)", "params": [2]},
        {"siid": 6, "aiid": 1, "name": "Start Self-Clean (Mode=Deep)", "params": [3]},
    ]

    print("="*60)
    print("TESTING DEVICE ACTIONS")
    print("="*60 + "\n")

    for action in test_actions:
        siid = action["siid"]
        aiid = action["aiid"]
        name = action["name"]
        params = action["params"]

        print(f"[*] Action: {name}")
        print(f"    siid: {siid}, aiid: {aiid}")
        print(f"    params: {params}")

        if args.dry_run:
            print("    [DRY RUN - Skipping execution]\n")
            continue

        try:
            response = execute_action(cloud, args.device_id, siid, aiid, params)

            print(f"    HTTP Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"    Response code: {result.get('code')}")

                if result.get("code") == 0:
                    print(f"    [+] SUCCESS!")
                    if "data" in result and "result" in result["data"]:
                        print(f"    Result: {result['data']['result']}")
                else:
                    print(f"    [!] Failed: {result.get('msg', 'Unknown error')}")
            else:
                print(f"    [!] HTTP Error: {response.text[:200]}")

        except Exception as ex:
            print(f"    [!] Exception: {ex}")

        print()

    print("="*60)
    print("SUMMARY")
    print("="*60)
    print("\nIf any action succeeded, note the siid/aiid and add it to const.py:")
    print("  HOLD_ACTION_START_SELF_CLEAN = ActionIdentifier(siid=X, aiid=Y, name=\"start_self_clean\")")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
