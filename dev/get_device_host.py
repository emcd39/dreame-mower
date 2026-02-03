#!/usr/bin/env python3
"""Get device host info and test actions."""

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


def main():
    parser = argparse.ArgumentParser(description="Get device host info")
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

    # Get device info (includes bindDomain)
    print("="*60)
    print("GETTING DEVICE INFO")
    print("="*60 + "\n")

    url = f"{cloud.get_api_url()}/{api[23]}/{api[24]}/{api[27]}/{api[29]}"
    data = {"did": args.device_id}

    headers = {
        "Content-Type": "application/json",
        api[46]: cloud._key,
    }
    if cloud._country == "cn":
        headers[api[48]] = api[4]

    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, ensure_ascii=False)}\n")

    response = cloud._session.post(url, json=data, headers=headers, timeout=30)

    print(f"HTTP Status: {response.status_code}\n")

    if response.status_code == 200:
        result = response.json()
        print(f"Response code: {result.get('code')}")

        if result.get("code") == 0 and "data" in result:
            device_info = result["data"]
            print(f"\n[+] Got device info:")
            print(json.dumps(device_info, indent=2, ensure_ascii=False))

            # Extract key fields
            if api[8] in device_info:  # masterUid
                print(f"\n[*] {api[8]} (UID): {device_info[api[8]]}")
            if api[35] in device_info:  # model
                print(f"[*] {api[35]} (Model): {device_info[api[35]]}")
            if api[9] in device_info:  # bindDomain (host)
                print(f"[*] {api[9]} (Host): {device_info[api[9]]}")

            # Try to get device props using the host
            if api[9] in device_info:
                host = device_info[api[9]]
                print(f"\n{'='*60}")
                print("TESTING ACTION WITH HOST")
                print('='*60 + "\n")

                # Build action URL with host
                host_prefix = f"-{host.split('.')[0]}" if host else ""
                action_url = f"{cloud.get_api_url()}/{api[37]}{host_prefix}/{api[27]}/{api[38]}"

                print(f"[*] Testing action endpoint:")
                print(f"    URL: {action_url}")
                print(f"    Host prefix: {host_prefix}")

                # Try a simple action
                action_data = {
                    "did": str(args.device_id),
                    "id": 1,
                    "data": {
                        "did": str(args.device_id),
                        "id": 1,
                        "method": "action",
                        "params": {
                            "did": str(args.device_id),
                            "siid": 5,
                            "aiid": 1,
                            "in": [],
                        }
                    }
                }

                print(f"    Action: Start cleaning (siid=5, aiid=1)")
                print(f"    Data: {json.dumps(action_data, ensure_ascii=False)}\n")

                try:
                    action_response = cloud._session.post(
                        action_url,
                        json=action_data,
                        headers=headers,
                        timeout=30
                    )

                    print(f"HTTP Status: {action_response.status_code}")

                    if action_response.status_code == 200:
                        action_result = action_response.json()
                        print(f"Response code: {action_result.get('code')}")
                        print(f"Response: {json.dumps(action_result, indent=2, ensure_ascii=False)[:500]}...")

                        if action_result.get("code") == 0:
                            print("\n[+] ACTION SUCCEEDED!")
                        else:
                            print(f"\n[!] Action failed: {action_result.get('msg', 'Unknown error')}")
                    else:
                        print(f"[!] HTTP Error: {action_response.text[:200]}")

                except Exception as ex:
                    print(f"[!] Exception: {ex}")
        else:
            print(f"[!] Failed to get device info: {result.get('msg', 'Unknown error')}")
    else:
        print(f"[!] HTTP Error: {response.text[:200]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
