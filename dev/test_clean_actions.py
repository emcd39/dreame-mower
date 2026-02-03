#!/usr/bin/env python3
"""Test self-clean actions with correct host info."""

import argparse
import json
import sys
import time
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


def execute_action(cloud, device_id, host, siid, aiid, params=None, description=""):
    """Execute a device action with correct host."""
    api = cloud._api_strings

    # Build action URL with host prefix
    host_prefix = f"-{host.split('.')[0]}" if host else ""
    url = f"{cloud.get_api_url()}/{api[37]}{host_prefix}/{api[27]}/{api[38]}"

    data = {
        "did": str(device_id),
        "id": int(time.time() * 1000),  # Use timestamp as ID
        "data": {
            "did": str(device_id),
            "id": int(time.time() * 1000),
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
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Language": "en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        api[47]: api[3],  # User-Agent
        api[49]: api[5],  # Authorization (Basic)
        api[50]: cloud._ti if cloud._ti else api[6],  # Tenant-Id
        api[51]: api[52],  # Content-Type: application/json (overrides above!)
        api[46]: cloud._key,  # Dreame-Auth token
    }
    if cloud._country == "cn":
        headers[api[48]] = api[4]

    print(f"    URL: {url}")
    print(f"    siid={siid}, aiid={aiid}, params={params}")

    # Serialize data as JSON string (not as JSON object)
    data_str = json.dumps(data, separators=(",", ":"))

    try:
        response = cloud._session.post(url, data=data_str, headers=headers, timeout=30)

        print(f"    HTTP Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"    Response code: {result.get('code')}")

            if result.get("code") == 0:
                print(f"    [+] ✓ SUCCESS! {description}")
                return True
            else:
                msg = result.get('msg', 'Unknown error')
                print(f"    [-] ✗ Failed: {msg}")
                return False
        else:
            print(f"    [!] HTTP Error: {response.text[:100]}")
            return False

    except Exception as ex:
        print(f"    [!] Exception: {ex}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test self-clean actions")
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

    api = cloud._api_strings

    # Get device info
    print("[*] Getting device info...")
    url = f"{cloud.get_api_url()}/{api[23]}/{api[24]}/{api[27]}/{api[29]}"
    data = {"did": args.device_id}

    headers = {
        "Content-Type": "application/json",
        api[46]: cloud._key,
    }
    if cloud._country == "cn":
        headers[api[48]] = api[4]

    response = cloud._session.post(url, json=data, headers=headers, timeout=30)

    if response.status_code != 200 or response.json().get("code") != 0:
        print("[!] Failed to get device info")
        return 1

    device_info = response.json()["data"]
    host = device_info.get(api[9], "")
    model = device_info.get(api[35], "")
    feature = device_info.get("deviceInfo", {}).get("feature", "")

    print(f"[+] Device: {model}")
    print(f"[+] Host: {host}")
    print(f"[+] Feature: {feature}")
    print()

    # Test actions
    # Based on the feature "hold_selfClean_selfCleanDeep", we should test:
    # - siid 6: Self-clean (common for mop cleaning)
    # - siid 7: Drying
    # - siid 5: Main cleaning controls
    # - siid 4: Status/Mode controls

    test_actions = [
        # Try different siid values for self-clean
        {"siid": 4, "aiid": 1, "params": [], "desc": "Start from siid=4"},
        {"siid": 5, "aiid": 1, "params": [], "desc": "Start cleaning (siid=5, aiid=1)"},
        {"siid": 5, "aiid": 2, "params": [], "desc": "Stop cleaning (siid=5, aiid=2)"},

        # Self-clean attempts
        {"siid": 6, "aiid": 1, "params": [], "desc": "Self-clean (siid=6, aiid=1)"},
        {"siid": 6, "aiid": 2, "params": [], "desc": "Self-clean stop (siid=6, aiid=2)"},
        {"siid": 6, "aiid": 3, "params": [], "desc": "Self-clean aiid=3"},
        {"siid": 6, "aiid": 4, "params": [], "desc": "Self-clean aiid=4"},

        # Self-clean with mode parameters
        {"siid": 6, "aiid": 1, "params": [1], "desc": "Self-clean mode=1 (Normal)"},
        {"siid": 6, "aiid": 1, "params": [2], "desc": "Self-clean mode=2 (Hot)"},
        {"siid": 6, "aiid": 1, "params": [3], "desc": "Self-clean mode=3 (Deep)"},

        # Drying attempts
        {"siid": 7, "aiid": 1, "params": [], "desc": "Drying (siid=7, aiid=1)"},
        {"siid": 7, "aiid": 2, "params": [], "desc": "Drying stop (siid=7, aiid=2)"},
        {"siid": 7, "aiid": 1, "params": [1], "desc": "Drying mode=1"},
        {"siid": 7, "aiid": 1, "params": [2], "desc": "Drying mode=2"},

        # Try higher siids (some devices use these for dock functions)
        {"siid": 16, "aiid": 1, "params": [], "desc": "siid=16, aiid=1"},
        {"siid": 17, "aiid": 1, "params": [], "desc": "siid=17, aiid=1"},
        {"siid": 18, "aiid": 1, "params": [], "desc": "siid=18, aiid=1"},
    ]

    print("="*70)
    print("TESTING ACTIONS")
    print("="*70)
    print("\nNOTE: Error 80001 means device is offline/sleeping.")
    print("      Wake up the device first for accurate testing.\n")

    successful_actions = []

    for i, action in enumerate(test_actions, 1):
        siid = action["siid"]
        aiid = action["aiid"]
        params = action["params"]
        desc = action["desc"]

        print(f"\n[{i}/{len(test_actions)}] Testing: {desc}")

        success = execute_action(cloud, args.device_id, host, siid, aiid, params, desc)

        if success:
            successful_actions.append({
                "siid": siid,
                "aiid": aiid,
                "params": params,
                "desc": desc
            })

        time.sleep(0.5)  # Small delay between requests

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70 + "\n")

    if successful_actions:
        print(f"[+] Found {len(successful_actions)} working actions:\n")
        for action in successful_actions:
            print(f"  {action['desc']}")
            print(f"    ActionIdentifier(siid={action['siid']}, aiid={action['aiid']}, name=\"{action['desc']}\")")
            print()

        print("Add these to const.py:")
        for action in successful_actions:
            name = action['desc'].lower().replace(' ', '_').replace('=', '_').replace(',', '')
            print(f'  HOLD_ACTION_{name.upper()} = ActionIdentifier(siid={action["siid"]}, aiid={action["aiid"]}, name="{name}")')
    else:
        print("[!] No successful actions found.")
        print("\nPossible reasons:")
        print("  1. Device is offline or in deep sleep")
        print("  2. Device doesn't support these actions via cloud API")
        print("  3. Need to use MQTT instead of HTTP API")
        print("\nRecommendation:")
        print("  - Wake up the device by pressing power button")
        print("  - Use mitmproxy to capture app traffic (see PACKET_CAPTURE_GUIDE.md)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
